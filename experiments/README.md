# Experiments — Reviewer Calibration

This folder contains the **falsification experiment** for CAA's central claim (H1): that the paired *recall / false-positive* metric, measured against a corpus of real incidents, discriminates good reviewers from bad ones.

## Files

- **`calibration-protocol-ptbr.md`** — the full protocol: matched-pair corpus construction, the four reviewer conditions (including two degenerate controls), metrics, and the pre-registered decision criteria. *(Currently in PT-BR; an EN translation is a welcome contribution.)*
- **`calib_experiment.py`** — a runnable skeleton against the Anthropic API. Reads a corpus of paired cases, runs four reviewer conditions over each, judges category match, and reports recall, false-positive rate, and the Youden index per reviewer, then checks the pre-registered criteria.

## Why two degenerate controls

The decisive control is the **over-flagger** (R4): it will score high recall *and* high false-positive rate. A single-metric calibration regime would pass it. If the experiment can only distinguish a good reviewer from a bad one using the *pair* of metrics, that is the evidence that the pairing — not either metric alone — is the contribution.

## Running it

```bash
export ANTHROPIC_API_KEY=...
pip install anthropic
python calib_experiment.py --corpus corpus/ --out results/
```

The `corpus/` directory is **not included** — building it (15 blinded matched pairs from public postmortems such as the `danluu/post-mortems` collection and k8s.af) is the substantive work, and is described step by step in the protocol. Expected cost: ~2 days of corpus authoring + negligible API spend.

## Pre-registration note

The decision criteria in the protocol (§4) are fixed **before** running. This is deliberate: a calibration framework that let its own author fish for a favorable result would fail its own standard. Results — corroborating or falsifying — should be committed here alongside the corpus that produced them.
