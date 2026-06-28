# Experiments — reviewer calibration falsification study

This folder contains the full data and code for the five-run falsification study described in `../docs/papers/empirical-study.md` and `../docs/technical-report.md`. Every numeric claim in those documents is reconstructable from the raw per-call records here, independently of the harness.

## What is here

**Corpora** (matched incident pairs; each `par_*.json` is one failure case + one healthy twin):
- `corpus/` — 15-pair pilot (first iteration; superseded)
- `corpus-v2/` — 20 pairs (Corpus A in the papers)
- `corpus-v3/` — 20 pairs (Corpus B in the papers), human-audited over three rewrites

**Runs** (each holds `raw_results.json`, `run-log.jsonl` with per-call `dry_run` provenance, `scores.json`, and `criteria-*.json`):
- `results/` — pilot run on the 15-pair corpus
- `results-v2/` — **real** run, Corpus A (iteration 2)
- `results-v3/` — **real** run, iteration 3.0 (R5_confident_wrong collapses into over-flagging)
- `results-v3-1/` — **real** run, Corpus B (iteration 3.1, the final run reported)
- `results-v3-1-dryrun/` — the contaminated **dry-run** (kept deliberately: this is the run that was caught as mock data; see the saga)

**Pre-registrations** (criteria fixed before each run): `preregistration-v2.md`, `preregistration-v3.md`, `preregistration-v3-1.md`

**Harness** (evolved across iterations): `calib_experiment.py`, `_v2.py`, `_v3.py`, `_v3_1.py`. The current study corresponds to `calib_experiment_v3_1.py`. Reviewer model: `claude-sonnet-4-6`; judge model: `claude-haiku-4-5` (distinct, logged per call).

**Other**: `r5-misattribution-manifest-v3-1.md` (the R5 displacement map), `iteration-3-1-investigation.md` (root-cause of the dry-run and R1 issues), `results-summary*.md`, `calibration-protocol-ptbr.md` (protocol in PT-BR).

## Reproducing a number

Each run's metrics can be recomputed from its `raw_results.json` alone:
- **recall** = fraction of `case_fail` rows where `flagged` and `primary_match` are both true;
- **false-positive rate** = fraction of `case_healthy` rows where both are true;
- **Youden** = recall − false-positive rate.

Check `run-log.jsonl` for `dry_run: false` on every row before trusting a run as real — this is the provenance check that the dry-run contamination defeated, and that an independent reader (not the gate) must perform.

## Headline numbers (reconstructed from raw)

| Reviewer | Corpus A recall/FP | Corpus B recall/FP |
|---|---|---|
| R2 contract | 1.00 / 0.05 | 1.00 / 0.10 |
| R1 naive | 1.00 / 0.25 | 1.00 / 0.55 |
| R3_narrow | 0.35 / 0.00 | 0.30 / 0.05 |
| R4 over-flagger | 1.00 / 1.00 | 1.00 / 1.00 |
| R5 misattribution | — | 0.00 / 0.00 (VOID) |

Note the reviewer-condition naming evolved across iterations: the pilot used a coarser set; the reported study uses R1 naive, R2 contract, R3_narrow (coverage gap), R4 over-flagger, and the R5 misattribution attempt. The earlier `R5_confident_wrong` (visible in `results-v3/`) is the persona that collapsed into over-flagging — the first of three failed attempts to construct a misattribution control.
