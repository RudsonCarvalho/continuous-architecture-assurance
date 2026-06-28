# Iteration 3.1 Investigation

Scope: investigation of the 3.1 dry-run artifact available locally at `experiments/results-v3-1-dryrun/`. No real API run was executed during this investigation.

## Q1: R1_naive silence

Local evidence:

- `run-log.jsonl` has 200 rows and all rows have `dry_run=true`.
- R1 rows in `raw_results.json`: 40/40 `verdict=PASS`, `flagged=false`, `findings=[]`.
- Example R1 row: `pair=V3-01`, `variant=case_fail`, `verdict=PASS`, `flagged=false`, `primary_match=false`, `findings=[]`.
- Example R1 log row: `case=V3-01`, `variant=case_fail`, `dry_run=true`, `verdict=PASS`, `parse_error=null`, `schema_errors=[]`.

Prompt comparison:

- `R1_naive` prompt in `calib_experiment_v3.py` and `calib_experiment_v3_1.py` is byte-for-byte identical.
- Prompt length is 1152 characters in both files.

Root cause:

- This was a dry-run harness bug, not an R1 prompt change and not parser loss. `dry_run_verdict()` in 3.1 had no explicit R1 branch, so R1 fell through to the default `PASS` response for every case.

Fix:

- Add a deterministic dry-run R1 branch that flags a stable subset of `case_fail` rows and no `case_healthy` rows. This exercises the harness without simulating either silence or saturation.

## Q2: R5_misattribution as pure noise

Local evidence:

- R5 rows: 40/40 flagged, 0/40 primary matches, 0/40 secondary matches.
- R5 score: `recall=0.0`, `fp_rate=0.0`, `flagged_rate=1.0`.
- The first-map implementation skipped primary, secondary and distractor categories, so it structurally prevented plausible collisions with the review labels.

Root cause:

- The initial map was a cyclic displacement plus an exclusion set that was too broad. It guaranteed wrongness but not plausible misattribution.

Fix:

- Replace the cyclic map with a documented affinity map:
  - T01 -> T04
  - T02 -> T07
  - T03 -> T10
  - T04 -> T10
  - T05 -> T09
  - T06 -> T09
  - T07 -> T11
  - T08 -> T05
  - T09 -> T12
  - T10 -> T12
  - T11 -> T02
  - T12 -> T02
- The harness now blocks only the identified category and the primary ground truth. Secondary and distractor categories are allowed, and non-trivial collision with them is measured as plausibility.

## Q3: Gate hardening

Previous gap:

- `corpus_validity_r1_unsaturated=true` treated R1 silence as valid because it only checked `recall < 1.00`.
- `manipulation_r5=true` accepted `recall=0`, `fp=0`, `flagged=1.0` without checking whether the emitted categories were plausibly related.

Fix:

- R1 validity now requires both:
  - `recall < 1.00`
  - non-silence: `flagged_rate > 0` and `recall > 0`
- R5 manipulation now requires:
  - `recall <= 0.40`
  - `flagged_rate >= 0.80`
  - `fp_rate > 0` OR `plausible_misattribution_rate >= 0.20`
- `plausible_misattribution_rate` is the fraction of flagged rows whose category matches `secondary` or `distractor_category`.

Verification:

- `pytest tests/test_calib_experiment_v3.py tests/test_calib_experiment_v3_1.py` passes.
- Temporary dry-run on frozen `corpus-v3` after the fix: R1 `recall=0.85`, `flagged_rate=0.425`; R5 `recall=0.00`, `flagged_rate=1.00`, `plausible_misattribution_rate=0.70`; no parse/schema/judge/call errors.
