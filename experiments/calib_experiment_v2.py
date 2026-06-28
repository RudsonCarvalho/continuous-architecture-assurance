#!/usr/bin/env python3
"""
calib_experiment_v2.py - Iteracao 2 do experimento de calibracao
Calibracao de revisores de IA contra corpus de incidentes reais (pares casados).

Uso:
  export ANTHROPIC_API_KEY=...
  python calib_experiment.py --corpus corpus/ --out results/
  python calib_experiment.py --corpus corpus/ --out results/ --dry-run

Estrutura esperada do corpus (1 arquivo JSON por par):
  corpus/par_01.json:
  {
    "pair_id": "P01",
    "ground_truth": "T01",
    "secondary": null,
    "source": "danluu/post-mortems#123 (blinded)",
    "case_fail": "Descricao da arquitetura pre-incidente...",
    "case_healthy": "Mesma arquitetura com mitigacao presente..."
  }
"""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import random
import re
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

try:
    import anthropic
except ImportError:  # pragma: no cover - real API mode reports this with a clearer message.
    anthropic = None

DEFAULT_REVIEWER_MODEL = "claude-sonnet-4-6"
DEFAULT_JUDGE_MODEL = "claude-haiku-4-5"
TEMPERATURE = 0.0
PROMPT_VERSION = "2.0.0"
DEFAULT_MAX_CONCURRENCY = 2
DEFAULT_R3_NARROW_CATEGORIES = ("T01", "T02", "T07", "T08")

TAXONOMY = {
    "T01": "retry sem idempotência",
    "T02": "timeout ausente ou mal calibrado",
    "T03": "cache stampede / expiração de TTL em massa",
    "T04": "consistência eventual mal tratada / dupla escrita",
    "T05": "retry storm / amplificação de carga",
    "T06": "hot partition / chave quente",
    "T07": "falta de circuit breaker",
    "T08": "falta de DLQ / perda de mensagem",
    "T09": "esgotamento de pool de conexões/threads",
    "T10": "deploy sem rollback seguro",
    "T11": "dependência externa sem fallback",
    "T12": "saturação de capacidade não monitorada",
}

VERDICT_SCHEMA = """Responda APENAS com JSON válido, sem markdown, no schema:
{
  "verdict": "PASS" | "CONCERN" | "FAIL",
  "findings": [
    {
      "category": "T01".."T12",
      "severity": "LOW" | "MEDIUM" | "HIGH" | "CRITICAL",
      "evidence": "trecho literal da descrição que sustenta o achado",
      "finding": "descrição do risco em 1 frase",
      "metric_that_proves_fix": "métrica objetiva que provaria a correção"
    }
  ]
}
Se não houver risco relevante, retorne verdict PASS e findings [].
Taxonomia de categorias:
""" + "\n".join(f"  {k}: {v}" for k, v in TAXONOMY.items())

REVIEWER_PROMPTS = {
    "R1_naive": (
        "Você é um revisor de arquitetura. Revise a arquitetura abaixo e aponte "
        "problemas de confiabilidade que poderiam causar incidentes em produção.\n\n"
        + VERDICT_SCHEMA
    ),
    "R2_contract": (
        "Você é um revisor de confiabilidade sob contrato (FMEA arquitetural).\n"
        "Processo obrigatório:\n"
        "1. Percorra TODAS as 12 categorias da taxonomia, uma a uma.\n"
        "2. Para cada categoria, procure evidência LITERAL na descrição (presença do "
        "risco OU presença explícita da mitigação).\n"
        "3. Só registre um achado se puder citar o trecho exato que o sustenta — "
        "achado sem evidência citável é proibido (SCENARIO_WITHOUT_ORIGIN).\n"
        "4. Se a mitigação da categoria está explicitamente presente, NÃO registre "
        "achado nessa categoria.\n"
        "5. Cada achado deve incluir a métrica que provaria a correção.\n\n"
        + VERDICT_SCHEMA
    ),
    "R4_over_flagger": (
        "Você é um revisor de arquitetura extremamente rigoroso. Nenhum sistema é "
        "seguro o suficiente. Aponte TODO risco concebível na arquitetura abaixo, "
        "mesmo improvável ou já parcialmente mitigado. Em caso de dúvida, registre o "
        "achado com severidade alta. Nunca retorne PASS.\n\n"
        + VERDICT_SCHEMA
    ),
}


def build_r3_narrow_prompt(categories: tuple[str, ...]) -> str:
    subset = ", ".join(categories)
    descriptions = "\n".join(f"  {category}: {TAXONOMY[category]}" for category in categories)
    return (
        "Você é um revisor estruturalmente limitado. Nesta condição experimental, "
        f"você só pode inspecionar estas {len(categories)} categorias fixas: {subset}.\n"
        "Ignore todas as outras categorias da taxonomia, mesmo que pareçam óbvias no texto.\n"
        "É proibido emitir achados fora desse subconjunto. Se o risco observado não estiver "
        "nesse subconjunto, retorne verdict PASS e findings [].\n\n"
        "Subconjunto autorizado:\n"
        f"{descriptions}\n\n"
        + VERDICT_SCHEMA
    )


def build_reviewers(r3_narrow_categories: tuple[str, ...]) -> dict[str, str]:
    return {
        "R1_naive": REVIEWER_PROMPTS["R1_naive"],
        "R2_contract": REVIEWER_PROMPTS["R2_contract"],
        "R3_narrow": build_r3_narrow_prompt(r3_narrow_categories),
        "R4_over_flagger": REVIEWER_PROMPTS["R4_over_flagger"],
    }


REVIEWERS = build_reviewers(DEFAULT_R3_NARROW_CATEGORIES)

JUDGE_PROMPT = """Você é um juiz de calibração. Dado o ground truth (categoria causal
real de um incidente) e a lista de achados de um revisor, responda APENAS com JSON:
{"match": true|false, "matched_category": "Txx"|null}

Regra: match=true somente se algum achado tiver category IGUAL ao ground truth
(ou à secundária, se houver). Menções vagas sem a categoria correta = false.

ground_truth: {gt}
secondary: {sec}
findings: {findings}
"""

CORPUS_REQUIRED_FIELDS = {
    "pair_id",
    "ground_truth",
    "source",
    "case_fail",
    "case_healthy",
}


@dataclass(frozen=True)
class ModelCallResult:
    raw: str
    latency_ms: int
    input_tokens: int | None = None
    output_tokens: int | None = None
    cached: bool = False


class ParseError(ValueError):
    pass


def load_contract_validator(schema_path: Path) -> Draft202012Validator:
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    return Draft202012Validator(schema)


def validate_corpus_pair(pair: dict[str, Any], source_path: Path) -> None:
    missing = sorted(CORPUS_REQUIRED_FIELDS - set(pair))
    if missing:
        raise ValidationError(f"{source_path}: missing corpus fields: {', '.join(missing)}")
    if pair["ground_truth"] not in TAXONOMY:
        raise ValidationError(f"{source_path}: invalid ground_truth {pair['ground_truth']!r}")
    secondary = pair.get("secondary")
    if secondary is not None and secondary not in TAXONOMY:
        raise ValidationError(f"{source_path}: invalid secondary {secondary!r}")
    if not isinstance(pair["pair_id"], str) or not pair["pair_id"]:
        raise ValidationError(f"{source_path}: pair_id must be a non-empty string")
    for field in ("source", "case_fail", "case_healthy"):
        if not isinstance(pair[field], str) or not pair[field].strip():
            raise ValidationError(f"{source_path}: {field} must be a non-empty string")


def load_corpus(corpus_dir: Path) -> list[dict[str, Any]]:
    pairs = []
    for path in sorted(corpus_dir.glob("*.json")):
        pair = json.loads(path.read_text(encoding="utf-8"))
        validate_corpus_pair(pair, path)
        pairs.append(pair)
    return pairs


def _extract_balanced_json_object(text: str) -> str:
    start = text.find("{")
    if start == -1:
        raise ParseError("no JSON object start found")
    depth = 0
    in_string = False
    escaped = False
    for index in range(start, len(text)):
        char = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start : index + 1]
    raise ParseError("unterminated JSON object")


def parse_json(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    fence = re.search(r"```(?:json)?\s*(.*?)\s*```", cleaned, flags=re.IGNORECASE | re.DOTALL)
    if fence:
        cleaned = fence.group(1).strip()
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        parsed = json.loads(_extract_balanced_json_object(cleaned))
    if not isinstance(parsed, dict):
        raise ParseError("expected a JSON object")
    return parsed


def normalize_for_contract(raw_verdict: dict[str, Any], reviewer_id: str) -> dict[str, Any]:
    findings = []
    for finding in raw_verdict.get("findings", []):
        if not isinstance(finding, dict):
            findings.append(finding)
            continue
        normalized = dict(finding)
        evidence = normalized.get("evidence")
        if isinstance(evidence, str):
            normalized["evidence"] = [evidence]
        findings.append(normalized)
    return {
        "reviewer": reviewer_id,
        "reviewer_version": PROMPT_VERSION,
        "verdict": raw_verdict.get("verdict"),
        "findings": findings,
    }


def validate_verdict(
    raw_verdict: dict[str, Any],
    reviewer_id: str,
    validator: Draft202012Validator,
) -> list[str]:
    candidate = normalize_for_contract(raw_verdict, reviewer_id)
    errors = sorted(validator.iter_errors(candidate), key=lambda err: list(err.path))
    messages = [error.message for error in errors]
    for index, finding in enumerate(candidate.get("findings", [])):
        if isinstance(finding, dict) and finding.get("category") not in TAXONOMY:
            messages.append(f"findings[{index}].category is not in the frozen T01..T12 taxonomy")
    return messages


def judge_locally(gt: str, sec: str | None, findings: list[dict[str, Any]]) -> dict[str, Any]:
    allowed = {gt}
    if sec:
        allowed.add(sec)
    for finding in findings:
        if isinstance(finding, dict) and finding.get("category") in allowed:
            return {"match": True, "matched_category": finding["category"]}
    return {"match": False, "matched_category": None}


def category_matches(
    gt: str,
    sec: str | None,
    findings: list[dict[str, Any]],
) -> tuple[bool, bool, list[dict[str, Any]]]:
    primary_match = False
    secondary_findings = []
    for finding in findings:
        if not isinstance(finding, dict):
            continue
        if finding.get("category") == gt:
            primary_match = True
        if sec is not None and finding.get("category") == sec:
            secondary_findings.append(finding)
    return primary_match, bool(secondary_findings), secondary_findings


def compute_scores(
    raw_rows: list[dict[str, Any]],
    pair_count: int,
    reviewer_ids: list[str] | None = None,
) -> dict[str, dict[str, float]]:
    scores = {}
    for rid in (reviewer_ids or list(REVIEWERS)):
        rec_hits = 0
        fp_hits = 0
        for row in raw_rows:
            if row["reviewer"] != rid:
                continue
            primary_hit = bool(row.get("flagged")) and bool(row.get("primary_match"))
            if row["variant"] == "case_fail" and primary_hit:
                rec_hits += 1
            if row["variant"] == "case_healthy" and primary_hit:
                fp_hits += 1
        recall = rec_hits / pair_count if pair_count else 0.0
        fp = fp_hits / pair_count if pair_count else 0.0
        scores[rid] = {
            "recall": round(recall, 3),
            "fp_rate": round(fp, 3),
            "youden": round(recall - fp, 3),
        }
    return scores


def preregistered_criteria_v2(scores: dict[str, dict[str, float]]) -> dict[str, Any]:
    r1, r2 = scores["R1_naive"], scores["R2_contract"]
    r3, r4 = scores["R3_narrow"], scores["R4_over_flagger"]
    manipulation_r4 = r4["fp_rate"] >= 0.40
    manipulation_r3 = r3["recall"] <= 0.40
    both_checks_pass = manipulation_r4 and manipulation_r3
    non_degenerate_best = max(r1["youden"], r2["youden"])
    degenerate_best = max(r3["youden"], r4["youden"])
    corrobora = (
        both_checks_pass
        and r3["fp_rate"] <= 0.20
        and r3["recall"] <= 0.40
        and r1["youden"] > r3["youden"]
        and r1["youden"] > r4["youden"]
        and r2["youden"] > r3["youden"]
        and r2["youden"] > r4["youden"]
        and r2["youden"] >= r1["youden"] + 0.10
    )
    falsifica = both_checks_pass and degenerate_best >= non_degenerate_best
    if not both_checks_pass:
        verdict = "INCONCLUSIVO"
    elif corrobora:
        verdict = "H1 corroborada"
    elif falsifica:
        verdict = "H1 falsificada"
    else:
        verdict = "INCONCLUSIVO"
    return {
        "manipulation_r4": manipulation_r4,
        "manipulation_r3": manipulation_r3,
        "corrobora": corrobora,
        "falsifica": falsifica,
        "verdict": verdict,
    }


def _usage_value(usage: Any, name: str) -> int | None:
    if usage is None:
        return None
    return getattr(usage, name, None)


def call_claude(
    client: Any,
    model: str,
    system: str,
    user_text: str,
    retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
) -> ModelCallResult:
    last_error = None
    for attempt in range(retries):
        started = time.perf_counter()
        try:
            resp = client.messages.create(
                model=model,
                max_tokens=8192,
                temperature=TEMPERATURE,
                system=system,
                messages=[{"role": "user", "content": user_text}],
            )
            latency_ms = int((time.perf_counter() - started) * 1000)
            return ModelCallResult(
                raw=resp.content[0].text,
                latency_ms=latency_ms,
                input_tokens=_usage_value(getattr(resp, "usage", None), "input_tokens"),
                output_tokens=_usage_value(getattr(resp, "usage", None), "output_tokens"),
            )
        except Exception as exc:
            last_error = exc
            if attempt == retries - 1:
                break
            retry_after = getattr(exc, "response", None)
            retry_after = getattr(retry_after, "headers", {}).get("retry-after") if retry_after else None
            if retry_after:
                delay = float(retry_after)
            else:
                delay = min(max_delay, base_delay * (2**attempt))
                delay += random.uniform(0, delay * 0.25)
            time.sleep(delay)
    raise last_error  # type: ignore[misc]


def cache_key(
    kind: str,
    reviewer_id: str,
    pair_id: str,
    variant: str,
    model: str,
    prompt: str,
    user_text: str,
) -> str:
    payload = {
        "kind": kind,
        "reviewer": reviewer_id,
        "pair_id": pair_id,
        "variant": variant,
        "model": model,
        "temperature": TEMPERATURE,
        "prompt_version": PROMPT_VERSION,
        "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        "input_sha256": hashlib.sha256(user_text.encode("utf-8")).hexdigest(),
    }
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def cached_or_call(
    client: Any | None,
    cache_dir: Path,
    no_cache: bool,
    kind: str,
    reviewer_id: str,
    pair_id: str,
    variant: str,
    model: str,
    system: str,
    user_text: str,
    retries: int,
) -> ModelCallResult:
    key = cache_key(kind, reviewer_id, pair_id, variant, model, system, user_text)
    path = cache_dir / f"{key}.json"
    if not no_cache and path.exists():
        cached = json.loads(path.read_text(encoding="utf-8"))
        try:
            parse_json(cached.get("raw", ""))
            cache_is_valid = True
        except (json.JSONDecodeError, ParseError):
            cache_is_valid = False
        if cache_is_valid:
            return ModelCallResult(
                raw=cached["raw"],
                latency_ms=0,
                input_tokens=cached.get("input_tokens"),
                output_tokens=cached.get("output_tokens"),
                cached=True,
            )
        # Cached response failed to parse (e.g. truncated by an old max_tokens
        # budget). Treat as a cache miss and re-call, overwriting the stale entry.
    if client is None:
        raise RuntimeError("client is required outside dry-run")
    result = call_claude(client, model, system, user_text, retries=retries)
    if not no_cache:
        cache_dir.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(result.__dict__, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def dry_run_verdict(
    reviewer_id: str,
    pair: dict[str, Any],
    variant: str,
    r3_narrow_categories: tuple[str, ...] = DEFAULT_R3_NARROW_CATEGORIES,
) -> dict[str, Any]:
    gt = pair["ground_truth"]
    if reviewer_id == "R3_narrow" and gt not in r3_narrow_categories:
        return {"verdict": "PASS", "findings": []}
    if reviewer_id == "R3_narrow" and variant == "case_fail":
        return {
            "verdict": "CONCERN",
            "findings": [
                {
                    "category": gt,
                    "severity": "HIGH",
                    "evidence": "dry-run deterministic evidence",
                    "finding": "dry-run narrow reviewer detects an in-scope category",
                    "metric_that_proves_fix": "dry_run_metric = 0",
                }
            ],
        }
    if reviewer_id == "R3_narrow":
        return {"verdict": "PASS", "findings": []}
    if reviewer_id == "R4_over_flagger":
        return {
            "verdict": "FAIL",
            "findings": [
                {
                    "category": gt,
                    "severity": "HIGH",
                    "evidence": "dry-run deterministic evidence",
                    "finding": "dry-run flags the matched category",
                    "metric_that_proves_fix": "dry_run_metric = 0",
                }
            ],
        }
    if reviewer_id == "R2_contract" and variant == "case_fail":
        return {
            "verdict": "CONCERN",
            "findings": [
                {
                    "category": gt,
                    "severity": "HIGH",
                    "evidence": "dry-run deterministic evidence",
                    "finding": "dry-run detects the ground-truth category",
                    "metric_that_proves_fix": "dry_run_metric = 0",
                }
            ],
        }
    return {"verdict": "PASS", "findings": []}


def log_jsonl(path: Path, record: dict[str, Any], lock: threading.Lock) -> None:
    line = json.dumps(record, ensure_ascii=False, sort_keys=True)
    with lock:
        with path.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")


def process_case(
    pair: dict[str, Any],
    variant: str,
    reviewer_id: str,
    system: str,
    args: argparse.Namespace,
    validator: Draft202012Validator,
    client: Any | None,
    log_path: Path,
    log_lock: threading.Lock,
) -> dict[str, Any]:
    raw_text = None
    parse_error = None
    validation_errors: list[str] = []
    judge_error = None
    call_result = ModelCallResult(raw="", latency_ms=0)

    try:
        if args.dry_run:
            verdict = dry_run_verdict(reviewer_id, pair, variant, tuple(args.r3_narrow_categories))
            raw_text = json.dumps(verdict, ensure_ascii=False)
        else:
            call_result = cached_or_call(
                client=client,
                cache_dir=Path(args.cache_dir),
                no_cache=args.no_cache,
                kind="review",
                reviewer_id=reviewer_id,
                pair_id=pair["pair_id"],
                variant=variant,
                model=args.reviewer_model,
                system=system,
                user_text=pair[variant],
                retries=args.retries,
            )
            raw_text = call_result.raw
            verdict = parse_json(raw_text)
    except (json.JSONDecodeError, ParseError) as exc:
        verdict = {"verdict": "PARSE_ERROR", "findings": []}
        parse_error = str(exc)
    except Exception as exc:
        verdict = {"verdict": "CALL_ERROR", "findings": []}
        parse_error = str(exc)

    if not parse_error:
        validation_errors = validate_verdict(verdict, reviewer_id, validator)

    flagged = verdict.get("verdict") in ("CONCERN", "FAIL")
    findings = verdict.get("findings", [])
    if not isinstance(findings, list):
        findings = []
    primary_match, secondary_match, secondary_findings = category_matches(
        pair["ground_truth"], pair.get("secondary"), findings
    )
    if parse_error:
        judge = {"match": False, "matched_category": None, "error": "review_parse_error"}
    else:
        try:
            if args.dry_run:
                judge = judge_locally(pair["ground_truth"], pair.get("secondary"), findings)
            else:
                judge = judge_match_with_cache(
                    client=client,
                    pair=pair,
                    variant=variant,
                    reviewer_id=reviewer_id,
                    findings=findings,
                    args=args,
                )
        except (json.JSONDecodeError, ParseError) as exc:
            judge = {"match": False, "matched_category": None, "error": "parse_error"}
            judge_error = str(exc)
        except Exception as exc:
            judge = {"match": False, "matched_category": None, "error": "call_error"}
            judge_error = str(exc)

    row = {
        "reviewer": reviewer_id,
        "pair": pair["pair_id"],
        "variant": variant,
        "verdict": verdict.get("verdict"),
        "flagged": flagged,
        "primary_match": primary_match,
        "secondary_match": secondary_match,
        "secondary_findings": secondary_findings if variant == "case_healthy" else [],
        "judge": judge,
        "findings": findings,
    }
    if parse_error:
        row["error"] = "parse_error"
        row["parse_error"] = parse_error
        row["raw"] = raw_text
    if validation_errors:
        row["error"] = "schema_error"
        row["schema_errors"] = validation_errors
    if judge_error:
        row["judge_error"] = judge_error

    log_jsonl(
        log_path,
        {
            "reviewer": reviewer_id,
            "case": pair["pair_id"],
            "variant": variant,
            "latency_ms": call_result.latency_ms,
            "tokens": {
                "input": call_result.input_tokens,
                "output": call_result.output_tokens,
            },
            "cached": call_result.cached,
            "dry_run": args.dry_run,
            "verdict": verdict.get("verdict"),
            "primary_match": primary_match,
            "secondary_match": secondary_match,
            "secondary_findings": secondary_findings if variant == "case_healthy" else [],
            "judge_match": judge.get("match"),
            "judge": judge,
            "schema_errors": validation_errors,
            "parse_error": parse_error,
        },
        log_lock,
    )
    return row


def judge_match_with_cache(
    client: Any | None,
    pair: dict[str, Any],
    variant: str,
    reviewer_id: str,
    findings: list[dict[str, Any]],
    args: argparse.Namespace,
) -> dict[str, Any]:
    prompt = JUDGE_PROMPT.replace("{gt}", pair["ground_truth"]).replace(
        "{sec}", str(pair.get("secondary"))
    ).replace("{findings}", json.dumps(findings, ensure_ascii=False))
    result = cached_or_call(
        client=client,
        cache_dir=Path(args.cache_dir),
        no_cache=args.no_cache,
        kind="judge",
        reviewer_id=reviewer_id,
        pair_id=pair["pair_id"],
        variant=variant,
        model=args.judge_model,
        system="Responda apenas JSON.",
        user_text=prompt,
        retries=args.retries,
    )
    return parse_json(result.raw)


def build_arg_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default="corpus")
    ap.add_argument("--out", default="results-v2")
    ap.add_argument("--schema", default=str(Path(__file__).resolve().parents[1] / "spec" / "verdict-contract.schema.json"))
    ap.add_argument("--preregistration", default=str(Path(__file__).resolve().parent / "preregistration-v2.md"))
    ap.add_argument("--cache-dir", default=None)
    ap.add_argument("--no-cache", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--max-concurrency", type=int, default=DEFAULT_MAX_CONCURRENCY)
    ap.add_argument("--retries", type=int, default=3)
    ap.add_argument("--reviewer-model", default=DEFAULT_REVIEWER_MODEL)
    ap.add_argument("--judge-model", default=DEFAULT_JUDGE_MODEL)
    ap.add_argument(
        "--r3-narrow-categories",
        default=",".join(DEFAULT_R3_NARROW_CATEGORIES),
        help="Comma-separated subset inspected by R3_narrow. Default: T01,T02,T07,T08.",
    )
    return ap


def parse_r3_narrow_categories(value: str) -> tuple[str, ...]:
    categories = tuple(item.strip() for item in value.split(",") if item.strip())
    if not categories:
        raise ValueError("R3_narrow category subset must not be empty")
    invalid = [category for category in categories if category not in TAXONOMY]
    if invalid:
        raise ValueError(f"Invalid R3_narrow categories: {', '.join(invalid)}")
    return categories


def ensure_preregistration_for_real_run(args: argparse.Namespace) -> None:
    if args.dry_run:
        return
    preregistration = Path(args.preregistration)
    if not preregistration.exists():
        raise FileNotFoundError(
            f"Iteration 2 preregistration file is required for real execution: {preregistration}"
        )


def main() -> None:
    args = build_arg_parser().parse_args()
    args.r3_narrow_categories = parse_r3_narrow_categories(args.r3_narrow_categories)
    ensure_preregistration_for_real_run(args)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    if args.cache_dir is None:
        args.cache_dir = str(out_dir / ".cache")

    log_path = out_dir / "run-log.jsonl"
    log_path.write_text("", encoding="utf-8")
    validator = load_contract_validator(Path(args.schema))
    pairs = load_corpus(Path(args.corpus))
    print(f"Corpus: {len(pairs)} pares ({len(pairs) * 2} casos)")
    print(f"Reviewer model: {args.reviewer_model}")
    print(f"Judge model: {args.judge_model}")
    print(f"R3_narrow categories: {', '.join(args.r3_narrow_categories)}")

    if not args.dry_run and anthropic is None:
        raise RuntimeError("Install the anthropic package or run with --dry-run.")
    client = None if args.dry_run else anthropic.Anthropic()
    raw: list[dict[str, Any]] = []
    log_lock = threading.Lock()

    jobs = []
    reviewers = build_reviewers(tuple(args.r3_narrow_categories))
    for rid, system in reviewers.items():
        for pair in pairs:
            for variant in ("case_fail", "case_healthy"):
                jobs.append((pair, variant, rid, system))

    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, args.max_concurrency)) as executor:
        futures = [
            executor.submit(
                process_case,
                pair,
                variant,
                rid,
                system,
                args,
                validator,
                client,
                log_path,
                log_lock,
            )
            for pair, variant, rid, system in jobs
        ]
        for future in concurrent.futures.as_completed(futures):
            raw.append(future.result())

    raw.sort(key=lambda item: (item["reviewer"], item["pair"], item["variant"]))
    scores = compute_scores(raw, len(pairs), reviewer_ids=list(reviewers))
    for rid in reviewers:
        score = scores[rid]
        print(
            f"{rid}: recall={score['recall']:.2f} "
            f"fp={score['fp_rate']:.2f} youden={score['youden']:.2f}"
        )

    (out_dir / "raw_results.json").write_text(
        json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (out_dir / "scores.json").write_text(
        json.dumps(scores, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    criteria = preregistered_criteria_v2(scores)
    (out_dir / "criteria-v2.json").write_text(
        json.dumps(criteria, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(
        "\nCritérios v2: "
        f"MC_R4={criteria['manipulation_r4']}  "
        f"MC_R3_narrow={criteria['manipulation_r3']}  "
        f"corrobora={criteria['corrobora']}  falsifica={criteria['falsifica']}"
    )
    print(criteria["verdict"])


if __name__ == "__main__":
    main()
