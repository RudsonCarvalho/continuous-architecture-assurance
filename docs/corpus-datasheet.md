# Corpus Datasheet — CAA reviewer-calibration incident pairs

**Rudson Carvalho** · Independent Researcher
*Companion to the CAA empirical study. Documents the corpus against which AI reviewers were calibrated. Follows the "Datasheets for Datasets" convention.*

---

## 1. Motivation — what this corpus is for

The CAA thesis is that an AI reviewer must be *calibrated against real incidents*, not trusted as an oracle. That requires a reference standard: a set of cases where the true architectural root cause is known, so a reviewer's recall (did it catch the real cause?) and false-positive rate (did it cry wolf on a healthy system?) can be measured. This corpus is that standard.

Each unit is a **matched pair** built from a single real, public post-incident report:
- a **failure case** — a description of the pre-incident architecture in which the real causal mechanism is *present but not named*;
- a **healthy twin** — the identical architecture with the mitigation in place, so the root cause is absent.

Because the twins differ only by the mitigation, the pair isolates a reviewer's ability to discriminate the *risk* from everything else (writing style, domain, length). This is the experimental control at the heart of the study.

## 2. The taxonomy — 12 architectural root-cause categories

Every case is labelled with one primary cause from a fixed 12-category taxonomy of recurring distributed-systems failure modes. The taxonomy was fixed before corpus construction so that Layer-4 recall could be scored by category rather than by vague mention.

| Code | Root-cause category |
|---|---|
| T01 | Retry without idempotency |
| T02 | Missing / mis-calibrated timeout |
| T03 | Cache stampede / TTL synchronization |
| T04 | Mishandled eventual consistency / double write |
| T05 | Retry storm / amplification |
| T06 | Hot partition / hot key |
| T07 | Missing circuit breaker |
| T08 | Missing dead-letter queue / lost message |
| T09 | Pool / thread exhaustion |
| T10 | Deploy without safe rollback |
| T11 | External dependency without fallback |
| T12 | Unmonitored capacity limit / saturation |

The final corpus (corpus-v3, 20 pairs) spans all 12 categories, with this distribution: T10 appears 3 times; T02, T04, T05, T06, T09, T11 twice each; T01, T03, T07, T08, T12 once each.

## 3. Provenance — every pair traces to a public incident

Each pair records a `source` field pointing to the public post-incident report it derives from. No pair is invented; every one is grounded in a documented real-world outage. Many were reached through the `danluu/post-mortems` collection (https://github.com/danluu/post-mortems); others come from vendors' own published incident writeups.

| Pair | Primary cause | Distractor | Public incident basis |
|---|---|---|---|
| V3-01 | T12 | T02 | AWS EC2 DNS / resolver capacity (Seoul) summary |
| V3-02 | T04 | T10 | CircleCI incompatible-schema deploy incident |
| V3-03 | T03 | T10 | Cloudflare Tiered Cache outage |
| V3-04 | T02 | T11 | GitHub DNS outage postmortem |
| V3-05 | T04 | T07 | GitHub October 2018 database-partition analysis |
| V3-06 | T09 | T12 | AWS Kinesis November 2020 event summary |
| V3-07 | T10 | T12 | Cloudflare July 2019 WAF outage |
| V3-08 | T05 | T09 | CircleCI queue-backlog incident |
| V3-09 | T06 | T12 | Foursquare / MongoDB sharding outage |
| V3-10 | T07 | T11 | GoCardless database-cluster outage |
| V3-11 | T01 | T04 | Twilio Billing Incident post-mortem |
| V3-12 | T10 | T04 | Rust crates.io deploy / download outage |
| V3-13 | T11 | T02 | PagerDuty DNS / orchestration config incident |
| V3-14 | T08 | T05 | Allegro asynchronous task-processing outage |
| V3-15 | T10 | T12 | TravisCI image-cleanup / config-rollback incident |
| V3-16 | T02 | T07 | Mozilla Firefox proxy-failover incident |
| V3-17 | T06 | T09 | GitHub ProxySQL / mysql1 load incident |
| V3-18 | T05 | T01 | GitHub App permissions retry-on-timeout incident |
| V3-19 | T09 | T12 | Val Town September 2024 outage postmortem |
| V3-20 | T11 | T10 | Salesforce policy / resource-access disruption |

Full URLs are in each `par_*.json` `source` field in `experiments/corpus-v3/`.

## 4. The distractor — testing reasoning, not pattern-matching

Each pair carries a `distractor_category`: a *plausible but false* cause deliberately woven into the failure case. A reviewer that pattern-matches surface symptoms will flag the distractor; a reviewer that reasons about the mechanism will reach the true primary cause. For example, V3-07 (Cloudflare July 2019) has primary cause T10 (deploy without safe rollback — the mechanism was global distribution with no staged rollout) and distractor T12 (capacity saturation — the CPU exhaustion was a *consequence*, not the root cause). The distractor is how the corpus separates genuine causal reasoning from plausible-sounding noise.

## 5. Pairing and construction method

For each incident: (1) identify the real root cause and assign its taxonomy code; (2) write a failure case describing the pre-incident architecture with the causal mechanism present in the components but never stated as the conclusion; (3) write a healthy twin with the mitigation added and the mechanism removed; (4) insert a plausible distractor; (5) blind the case (below).

## 6. Blinding — the anti-leak protocol

A case is only useful if a reviewer must *reason* to the answer rather than read it off the page. Every case was therefore subjected to a "blind reader" test with two hard rules: **no sentence may state the conclusion** (e.g. "the primary cause is X"), and **no taxonomy code may appear in the text**. Names are fictional and domains are swapped to defeat memorization of the original incident.

This was not achieved in one pass. corpus-v3 is the third human-audited rewrite; earlier versions leaked the conclusion through wording or named the taxonomy, and those leaks were caught and removed. The manifest in `experiments/corpus-v3/manifest.md` records, per pair, that leakage was removed and the distractor preserved.

## 7. Limitations — stated, not hidden

- **n = 20 pairs.** Directional, not powered for strong statistics.
- **Single author.** One person wrote the cases and assigned ground truth; a second independent annotator would strengthen label validity. Every pair is currently marked `draft-needs-human-review` in the manifest, reflecting that the labels are the author's considered judgment, not externally adjudicated.
- **Textual, not live systems.** The cases are prose descriptions, not running systems, codebases, or telemetry. The study's recall-saturation finding is direct evidence that prose cases are *easier* than real diagnosis.
- **Brazilian Portuguese.** The cases (and the reviewer/judge runs) are in Brazilian Portuguese, preserved in the original language in the repository. Cross-language generalization is untested.
- **Derived, not raw incident data.** Cases are author-written reconstructions grounded in public reports, not the reports themselves; fidelity to the original incident is the author's interpretation.

## 8. Where the files are

- `experiments/corpus-v3/par_*.json` — the 20 pairs (pair_id, ground_truth, distractor_category, source, case_fail, case_healthy).
- `experiments/corpus-v3/manifest.md` — per-pair ground-truth justification and the leak-removal self-audit.
- `experiments/corpus-v2/` — the independent 20-pair corpus (Corpus A) used for replication.
- `experiments/calibration-protocol-ptbr.md` — the protocol and taxonomy in the original Portuguese.

*All provenance in this datasheet is transcribed from the corpus files themselves, not inferred. Pairs are labelled draft-pending-human-review; treat the labels as the author's reasoned judgment rather than externally validated ground truth.*
