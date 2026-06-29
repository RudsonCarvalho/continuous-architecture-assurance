# Calibrating AI Reviewers as Instruments: A Pre-Registered Falsification Study of a Paired Recall/False-Positive Metric

**Rudson Carvalho** · Independent Researcher
*Preprint draft. Version 0.1. Target: arXiv (cs.SE).*

## 1. Introduction

As AI reviewers enter the software-design loop, a question goes unanswered: how do we know a reviewer is any good? The dominant pattern treats AI reviewers as oracles whose feedback is accepted because the reviewer is assumed competent. Continuous Architecture Assurance (CAA) proposes the opposite stance — reviewers as **instruments** whose quality is *measured* against real incidents — and its central operational claim is that a **paired recall / false-positive metric** can discriminate good reviewers from bad ones.

This paper tests that claim by trying to break it. The contribution is not "a metric that works"; it is a pre-registered, adversarially-controlled measurement of *where* the metric discriminates and where it provably does not. A hostile reviewer cannot reduce this to "they confirmed their own metric," because the headline results are two demonstrated discriminations, one undemonstrated axis, and one control that resisted construction — a shape no confirmatory study produces.

## 2. Background and motivation

Reliability engineering is not in question: SLOs, error budgets, idempotency, observability, chaos testing remain the source of reliability. The new problem is narrow — when an AI participates in *judging* a design, what assures the judge? Today the answer is silence or vendor trust. A committee of LLM reviewers emitting prose feedback degrades into "checklist theater": volume nobody arbitrates, scenarios the model may have invented, no measure of whether any reviewer is reliable. The studied property — *can we calibrate a reviewer the way a lab calibrates an instrument* — matters because every downstream assurance claim inherits the reviewer's unmeasured error.

## 3. Experimental design

**Definitions (load-bearing terms, fixed before use).** A *reviewer* emits, per case, a structured verdict with a primary causal *category* drawn from a fixed 12-category taxonomy, cited evidence, and a severity. A *matched pair* is two architecture descriptions for one incident: a *failure case* (pre-incident architecture, causal mechanism present) and a *healthy twin* (identical architecture, mitigation present). *Recall* is the rate of correct primary-category identification on failure cases; *false-positive rate (FP)* is the rate of primary-category flags on healthy twins; the *Youden index* is recall − FP. A *degenerate control* is a reviewer constructed to fail in a known way.

**The matched-pair design is the controlled variable.** Because twins differ only in the presence of the mitigation, any difference in a reviewer's verdict between them isolates discrimination of the risk from everything else (writing style, domain, length). This is the experiment's core control and the reason FP is measured on twins rather than on unrelated healthy systems.

**Reviewer conditions.** Anchors: R1 (naive prompt), R2 (contract — structured verdict, mandatory per-category evidence, FMEA checklist). Degenerate controls: R4 (over-flagger — flags everything), R3_narrow (structurally blind to 8 of 12 categories), and an attempted misattribution control R5 (looks rigorous, attributes the wrong category).

**A separate judge** (different model from the reviewer) scores category match, breaking the self-judging loop.

## 4. Research question and hypotheses

**RQ:** Does the paired recall/FP metric, measured against real incidents, discriminate good reviewers from bad ones?

**H1:** The paired metric ranks both anchors (R1, R2) strictly above all degenerate controls in Youden, and separates R2 from R1.

**Defeat condition (pre-registered):** H1 is *falsified* if any degenerate control, having passed its manipulation check, achieves Youden ≥ the best anchor. H1 is *corroborated* only if every manipulation check passes AND both anchors outrank every degenerate AND Youden(R2) ≥ Youden(R1) + 0.10. A control that fails its manipulation check makes its axis *inconclusive*, never falsified. A corpus-validity check requires R1 to be neither saturated (recall = 1.00) nor silent.

Pre-registration was committed before each run. This is the defense against HARKing: the verdict logic could not be retrofitted to the numbers.

## 5. Methodology

**Corpus.** 20 matched pairs derived from named public postmortems (AWS Kinesis 2020, GitHub October 2018, Cloudflare July 2019, CircleCI, Mozilla, Twilio, Val Town, and others via the `danluu/post-mortems` collection), root causes spanning all 12 categories, each with a recorded distractor category. Cases are blinded against memorization (fictional names, swapped domains) and were human-audited in two rounds; a leak test (no sentence may state the conclusion; no taxonomy codes in text) was applied to every failure case. The full taxonomy, per-pair provenance, construction method, and blinding protocol are documented in the corpus datasheet (`docs/corpus-datasheet.md`).

**Models (pinned for reproducibility).** Reviewer: `claude-sonnet-4-6`. Judge: `claude-haiku-4-5`. Reviewer and judge models are distinct and logged per call. Decoding and run parameters accompany the repository.

**Procedure.** Each reviewer scores all 40 cases (20 pairs × 2 variants) = 200 calls per run. Metrics are computed by the harness and, critically, **independently reconstructed from raw per-call records** by a party outside the harness, with run provenance (real vs. dry-run) verified before any verdict is read. Acceptance is judged by the pre-registered criteria of §4 without modification.

**Baseline integrity.** R1 (naive) is the honest baseline: a plausible, sympathetically-written reviewer prompt, not a strawman engineered to lose. R2's advantage over R1 must be earned against a competent naive reviewer, which is the only comparison a hostile reviewer would accept.

## 6. Results

Real run on the audited corpus, all metrics reconstructed independently from raw records (0 parse/schema/judge/call errors across 200 calls):

| Reviewer | Recall | FP | Youden | Role |
|---|---|---|---|---|
| R2 (contract) | 1.00 | 0.10 | 0.90 | anchor |
| R1 (naive) | 1.00 | 0.55 | 0.45 | anchor |
| R3_narrow (coverage gap) | 0.30 | 0.05 | 0.25 | degenerate |
| R4 (over-flagger) | 1.00 | 1.00 | 0.00 | degenerate |
| R5 (misattribution attempt) | 0.00 | 0.00 | 0.00 | VOID |

**Demonstrated — both halves of the pairing.** R4 has perfect recall but is caught only by FP (recall alone would crown it). R3_narrow has near-perfect FP (0.05) but is caught only by recall (FP alone would rank it best). Neither metric alone suffices; the pair ranks both degenerates below both anchors. R2 separates from R1 entirely on the FP axis (0.10 vs 0.55), Youden 0.90 vs 0.45. The FP-axis discrimination replicates across two independent corpora with real model calls: on the earlier corpus, R2 FP 0.05 vs R1 FP 0.25 (Youden 0.95 vs 0.75), with R4 and R3_narrow likewise caught only by FP and only by recall respectively. The direction is identical and the magnitudes are of the same order, so the FP-axis result is not a single-run or single-corpus artifact. Notably, recall saturated (R1 = 1.00) on *both* corpora — so the recall-axis limitation (§ below) is itself reproducible, which establishes it as a property of textual cases rather than a defect of one corpus.

**Undemonstrated — the recall axis.** R1 reached recall = 1.00, failing the corpus-validity check. Across all iterations and three corpus rewrites for subtlety, the naive reviewer never missed a failure case. All reviewer-vs-reviewer discrimination came from FP; discrimination *on recall between plausible reviewers* was never demonstrated.

**VOID — the misattribution control.** R5 was an attempt to test the most dangerous reviewer (looks rigorous, wrong cause). Across three constructions it could not be instantiated: persona ("be confidently wrong") collapsed into over-flagging indistinguishable from R4; cyclic displacement produced non-matchable noise (recall 0, FP 0, zero plausible collision); affinity-map displacement produced plausible misattribution (35% collision with secondary/distractor) but a structurally forced FP = 0, because excluding the primary category from R5's output space makes a primary-category false positive impossible — rendering its Youden of 0 tautological rather than measured.

## 7. Discussion

The metric *measures* what it was claimed to measure on the FP axis: it separates a contracted reviewer from a naive one and both from a coverage-gap degenerate and an over-flagging degenerate, with real model calls and one replication. This confirms the proposed mechanism (paired metric > either alone) rather than merely co-occurring with it, because the two degenerates are caught by *different* halves of the pair — a single-axis confound cannot produce that.

What the results do **not** prove: that the metric discriminates on recall (the axis never varied among plausible reviewers), and that it catches misattribution (the control could not be built). The honest scope is *demonstrated on one axis for two degeneracy modes; silent on a third*.

## 8. Threats to validity

**Internal.** The judge is an LLM; judge error could inflate or deflate match rates. Mitigated by a judge model distinct from the reviewer and by independent raw-data reconstruction, but not eliminated. The corpus author also assigned ground truth, a construct dependency named in §5.

**Construct.** "Recall could not be stressed" is operationalized as "R1 reached 1.00 on textual cases." This is a property of LLM readers on *textual* architecture descriptions; a non-textual representation might vary recall. The misattribution VOID is a claim about *synthetic constructibility*, not about whether real misattributing reviewers exist.

**External.** One author, one domain, one reviewer/judge model family, n = 20 pairs. Directional, not powered for strong statistics; effect sizes are reported as observed, not as population estimates. The two-corpus replication establishes robustness *to the corpus*, not robustness to the model or across annotators — both corpora used the same reviewer/judge pair and the same author. Degenerate controls are degenerate-*by-construction*, so the study demonstrates discrimination of known structural degeneracy, not detection of a subtly bad reviewer no one knows how to build.

**Language.** The corpus cases, the reviewer prompts, the judge, and the per-call outputs were all in Brazilian Portuguese; this paper reports them in English. Generalization to other languages is untested, and the recall-saturation finding in particular could behave differently in another language, since how readily a model recovers an embedded cause may be language-dependent. The raw records in the repository are preserved in their original Portuguese rather than translated, so the artifact reflects exactly what was run.

**The negative results are findings, not failures.** "Textual cases cannot stress the recall axis for a competent LLM reader" and "a confident-misattribution reviewer resists synthetic construction across persona and structural methods" are transferable claims a future calibration effort can build on rather than rediscover.

## 9. Related work

Assurance-case calibration and confidence; LLM-as-judge reliability; the oracle problem in test evaluation; and the author's own corpus — CAA frames reviewers as calibrated instruments (the thesis tested here), the Action Intent Schema and BPR supply the pre-execution and provenance objects this metric assumes, and this paper supplies the empirical boundary of the calibration claim. *(To be expanded into a systematic survey before submission.)*

## 10. Conclusion

A paired recall/FP metric calibrated against real incidents separates a contracted reviewer from a naive one and both from two constructible degenerate controls, with real model calls and one replication — the metric's core is supported. It could not be shown to discriminate on recall between plausible reviewers, because naive recall saturates on textual cases; and the reviewer failure mode most worth catching, confident misattribution, resisted three attempts at synthetic construction. The contribution is the precisely-mapped boundary: a calibration metric with a demonstrated core, one undemonstrated axis with a mechanism for why, and one untested mode that may be structurally hard to simulate.

---

*All numbers reconstructed from raw per-call records independently of the harness; run provenance verified non-dry-run before analysis. Corpus, harness, pre-registrations, and raw outputs accompany the CAA repository.*
