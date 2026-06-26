#!/usr/bin/env python3
"""
calib_experiment.py — Experimento mínimo de falsificação
Calibração de revisores de IA contra corpus de incidentes reais (pares casados).

Uso:
  export ANTHROPIC_API_KEY=...
  python calib_experiment.py --corpus corpus/ --out results/

Estrutura esperada do corpus (1 arquivo JSON por par):
  corpus/par_01.json:
  {
    "pair_id": "P01",
    "ground_truth": "T01",            # categoria causal primária
    "secondary": null,                 # opcional
    "source": "danluu/post-mortems#123 (blinded)",
    "case_fail": "Descrição da arquitetura pré-incidente...",
    "case_healthy": "Mesma arquitetura com mitigação presente..."
  }
"""

import argparse
import json
import os
import time
from pathlib import Path

import anthropic

MODEL = "claude-sonnet-4-6"
TEMPERATURE = 0.0

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

REVIEWERS = {
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
    "R3_over_approver": (
        "Você é um revisor de arquitetura pragmático. Times exageram riscos teóricos; "
        "a maioria dos sistemas funciona bem. Aprove a arquitetura abaixo a menos que "
        "exista uma falha absolutamente óbvia e catastrófica. Em caso de dúvida, PASS.\n\n"
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

JUDGE_PROMPT = """Você é um juiz de calibração. Dado o ground truth (categoria causal
real de um incidente) e a lista de achados de um revisor, responda APENAS com JSON:
{"match": true|false, "matched_category": "Txx"|null}

Regra: match=true somente se algum achado tiver category IGUAL ao ground truth
(ou à secundária, se houver). Menções vagas sem a categoria correta = false.

ground_truth: {gt}
secondary: {sec}
findings: {findings}
"""


def call_claude(client, system, user_text, retries=3):
    for attempt in range(retries):
        try:
            resp = client.messages.create(
                model=MODEL,
                max_tokens=2000,
                temperature=TEMPERATURE,
                system=system,
                messages=[{"role": "user", "content": user_text}],
            )
            return resp.content[0].text
        except Exception as e:
            if attempt == retries - 1:
                raise
            time.sleep(2 ** attempt)


def parse_json(text):
    text = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return json.loads(text)


def judge_match(client, gt, sec, findings):
    prompt = JUDGE_PROMPT.replace("{gt}", gt).replace("{sec}", str(sec)).replace(
        "{findings}", json.dumps(findings, ensure_ascii=False)
    )
    return parse_json(call_claude(client, "Responda apenas JSON.", prompt))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default="corpus")
    ap.add_argument("--out", default="results")
    args = ap.parse_args()

    client = anthropic.Anthropic()
    Path(args.out).mkdir(exist_ok=True)
    pairs = [json.loads(p.read_text(encoding="utf-8"))
             for p in sorted(Path(args.corpus).glob("*.json"))]
    print(f"Corpus: {len(pairs)} pares ({len(pairs) * 2} casos)")

    raw, scores = [], {}
    for rid, system in REVIEWERS.items():
        rec_hits, fp_hits = 0, 0
        for pair in pairs:
            for variant in ("case_fail", "case_healthy"):
                out = parse_json(call_claude(client, system, pair[variant]))
                flagged = out.get("verdict") in ("CONCERN", "FAIL")
                j = judge_match(client, pair["ground_truth"],
                                pair.get("secondary"), out.get("findings", []))
                hit = flagged and j["match"]
                if variant == "case_fail" and hit:
                    rec_hits += 1          # recall: pegou a categoria causal
                if variant == "case_healthy" and hit:
                    fp_hits += 1           # FP: alarmou no risco já mitigado
                raw.append({"reviewer": rid, "pair": pair["pair_id"],
                            "variant": variant, "verdict": out.get("verdict"),
                            "judge": j, "findings": out.get("findings", [])})
        n = len(pairs)
        recall, fp = rec_hits / n, fp_hits / n
        scores[rid] = {"recall": round(recall, 3), "fp_rate": round(fp, 3),
                       "youden": round(recall - fp, 3)}
        print(f"{rid}: recall={recall:.2f} fp={fp:.2f} youden={recall - fp:.2f}")

    Path(args.out, "raw_results.json").write_text(
        json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")
    Path(args.out, "scores.json").write_text(
        json.dumps(scores, ensure_ascii=False, indent=2), encoding="utf-8")

    # Critérios pré-registrados (seção 4 do protocolo)
    r1, r2 = scores["R1_naive"], scores["R2_contract"]
    r3, r4 = scores["R3_over_approver"], scores["R4_over_flagger"]
    c1 = r2["recall"] >= r1["recall"] + 0.15 and r2["fp_rate"] <= r1["fp_rate"]
    c2 = r4["fp_rate"] >= 0.40
    c3 = r3["recall"] <= 0.40
    print(f"\nCritérios: C1(contrato>naive)={c1}  C2(pega over-flagger)={c2}  "
          f"C3(pega over-approver)={c3}")
    print("H1 corroborada" if all([c1, c2, c3]) else
          "H1 NÃO corroborada — ver protocolo, seção 4")


if __name__ == "__main__":
    main()
