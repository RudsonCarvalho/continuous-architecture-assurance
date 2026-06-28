# Continuous Architecture Assurance: Calibrating AI Reviewers as Instruments, Not Oracles

**Rudson Carvalho** · Independent research
*Position paper — draft for discussion. Version 0.1.*

## Abstract

As AI reviewers enter the software design loop, the dominant pattern is a committee of specialized LLM reviewers that emit free-form feedback before a system ships. This pattern treats the reviewers as oracles and leaves a question unanswered: who verifies that the reviewer is reliable? We propose **Continuous Architecture Assurance (CAA)**, an assurance layer that reframes the problem as one of *metrology*. CAA's contribution is not another framework for judging architecture, but a mechanism for calibrating such frameworks: AI reviewers (and any other "ruler") are treated as instruments that emit measurements under a fixed verdict contract, that are gated by objective rules with mandatory traceability, and that are themselves continuously calibrated against a corpus of real incidents using a paired recall / false-positive metric. We position CAA against the dynamic-assurance-case literature, the Evidential Tool Bus, ACCESS, Assurance 2.0, and recent work on LLM-generated assurance cases, arguing that the specific intersection CAA occupies — assurance-case rigor for mainstream distributed systems, with AI reviewers as calibrated instruments — is currently unoccupied. We are explicit that CAA's central efficacy claim is a falsifiable hypothesis, and we include a pre-registered experiment designed to falsify it.

## 1. Motivation

The advice to "use AI to design reliable systems at scale" typically resolves into a swarm of AI reviewers, each responsible for one concern (security, data consistency, capacity, and so on), each producing prose feedback on a proposed design. The framing is appealing because it mirrors how expert review boards work. In practice it tends to degrade into *checklist theater*: a volume of plausible-sounding output that no party arbitrates, frequently grounded in failure scenarios the model generated without any traceable source, and accepted because the reviewer is assumed competent.

Reliability engineering itself is not in question here. The SRE canon — service-level objectives, error budgets, idempotency, graceful degradation, observability, automated rollback, chaos testing — remains the source of reliability. The open problem is narrower and newer: when an AI system participates in *judging* whether a design is reliable, what assurance do we have about the judge?

This paper argues that the missing piece is not a better reviewer. It is a regime that treats reviewers as **instruments** and subjects them to the same discipline a metrology lab applies to a measuring device: calibration against a reference standard, declared measurement uncertainty, and a chain of custody from measurement back to origin.

## 2. The CAA proposal

### 2.1 What CAA produces

CAA produces a single artifact of value: *justified confidence with known coverage*. This is deliberately weaker than "the system will not fail" and deliberately stronger than a passing checklist. It states what was claimed, the evidence behind each claim, and the residual risk that was knowingly accepted because it was neither claimed nor tested.

### 2.2 Two planes and the independence principle

CAA separates a **production plane** — any process that produces code, decisions, and deployments, whether an agentic SDLC, an autonomous software factory, or a human team — from an **assurance plane** that consumes claims and evidence and emits auditable confidence. The interface between them is a verdict contract (§2.4).

The governing constraint is **independence**: the party that assures must not be the party that produces. A production pipeline's internal reviewers and quality gates are part of *production*; CAA audits them as well. The analogy is internal controls versus independent audit in financial institutions — the existence of the former does not discharge the need for the latter, and regulation requires both.

### 2.3 The pipeline

CAA organizes the assurance plane into five layers plus a deterministic triage step. We summarize them; the accompanying diagram (`docs/pipeline-v2-diagram.svg`) shows the full flow and the two feedback loops.

- **Layer 0 — Indexing & traceability.** Inputs are indexed and every critical journey, expected behavior, and constraint is assigned an origin identifier (EX-ID) pointing to the exact source passage or to a real incident. The invariant *no scenario without an origin* is enforced downstream: a finding without a traceable origin is rejected as `SCENARIO_WITHOUT_ORIGIN`. This directly addresses model-invented scenarios that imitate rigor while being unauditable.

- **Risk-class triage (deterministic).** A non-LLM step classifies the change by risk and routes the mandatory subset of reviewers, in a fixed order. This bounds cost and removes the possibility of the model silently skipping a required review.

- **Layer 1 — Reviewers under contract.** Reviewers emit only structured verdicts (§2.4); free prose is discarded. The reviewer set is conventional; the constraint on their *output* is the novelty.

- **Layer 2 — Arbiter & objective gates.** An arbiter resolves inter-reviewer conflict by severity weighted by risk class, escalating ties on critical changes to a human. Four gates (traceability, failure-mode coverage, falsifiable ADRs, production readiness) yield a GO / NO-GO decision with an evidence trail.

- **Layer 3 — Runtime governance.** Production agents act under a pre-execution cycle: a scoped mandate, an explicit intent declaration prior to action, a capability classification (read / write / effectful / irreversible) with verification proportional to the class, and execution under an audit trail. Telemetry feeds backward: incidents enter the evaluation corpus and production metrics trip the `reassess_when` conditions on prior decisions.

- **Layer 4 — Evaluations of the reviewers.** Reviewers carry their own quality contract. The corpus is composed of real incidents and postmortems. Two metrics are reported as an inseparable pair: recall of known risks and false-positive rate. A reviewer version is promoted only if it improves both.

### 2.4 The verdict contract

The verdict contract is the pluggable interface and, we argue, the actual product. Each verdict fixes a small set of fields: an enumerated verdict and severity; an `evidence` list of origin identifiers; the `metric_that_proves_fix`; and a `reassess_when` condition. Two of these fields do disproportionate work. `metric_that_proves_fix` prevents decorative architecture — a recommendation with no metric that would demonstrate its success does not close. `reassess_when` converts each architectural decision into a hypothesis with explicit revisiting conditions, inheriting the strongest idea from prior reliability-review practice ("the metric that would indicate this decision has failed"). A machine-readable schema is provided in `spec/verdict-contract.schema.json`.

### 2.5 The metrology framing

The framing that unifies the design is metrological. A reviewer is an instrument. Calibration is recall and false-positive rate measured against a reference standard of real incidents. Measurement uncertainty is the explicit residual risk. Metrological traceability is the origin rule. The chain of custody is the verdict contract plus audit trail. The consequence is that CAA is deliberately *ruler-agnostic*: a well-architected framework, an internal checklist, or the ten-reviewer committee above are all admissible instruments, provided they accept calibration and emit measurements under contract. The party that calibrates must be independent of the parties that manufacture rulers — which is precisely why the space is empty, since a ruler vendor has no incentive to build the mechanism that can fail its own ruler.

## 3. Related work and positioning

**Dynamic / through-life assurance cases.** Continuous assurance has been studied as dynamic assurance cases, runtime certification, adaptive safety cases, through-life assurance, and Assurance 2.0. Denney, Pai and colleagues introduced dynamic assurance cases with runtime confidence quantification; the ACCESS method converts portions of an assurance case into dynamic form with automated, non-invasive runtime evaluation; and dynamic-safety-case frameworks extend safety-management to continuous, through-life updates. This body of work is the closest in spirit to CAA. It differs in domain (autonomous vehicles, UAS, medical devices) and in authorship: assurance arguments are still largely specified manually by safety engineers, and tooling such as AdvoCATE supports construction but not continuous maintenance. CAA borrows the claim–argument–evidence discipline and the design-time/runtime/evolution-time lifecycle, and relocates it to mainstream distributed-systems reliability.

**Automated assurance-case construction.** The Evidential Tool Bus enables decentralized, continuous assurance workflows; automated assurance-case generation tools instantiate cases from a curated evidence store but lack mechanisms for dynamic maintenance. CAA differs by not aiming to *generate the case* automatically; it constrains the *output* of evidence-producing components and validates those components.

**LLM-generated assurance cases.** Recent studies (2024–2025) show that GPT-class models can instantiate assurance cases that comply with a formalized pattern, while concluding that they fall short of human experts and that a semi-automatic approach is currently more practical. The crucial distinction is the role of the model: in that line the LLM is the *author* of the assurance case; in CAA the LLM is a *governed evidence producer*, constrained by the verdict contract, the origin rule, the arbiter, and — most importantly — its own calibration in Layer 4.

**AI-driven architecture governance (industry).** Practitioner and analyst writing describes closed-loop continuous architecture governance, with agents ingesting CI/CD signals into a living architecture graph and delivering "continuous assurance" for enterprise architecture. This work is largely aspirational and lacks assurance-case semantics, a verdict contract, an origin rule, and any meta-evaluation of the reviewers. CAA can be read as the missing formal substrate beneath that vision.

**The empty intersection.** No surveyed line occupies the intersection of: (i) assurance-case rigor, (ii) mainstream distributed systems rather than safety-critical, (iii) AI reviewers as calibrated instruments rather than authors or oracles, and (iv) evaluation of the reviewers as a first-class, paired-metric concern. This intersection is CAA's claimed contribution.

## 4. Falsifiable claim and experiment

CAA's central efficacy claim is **H1**: the paired recall / false-positive metric, measured against a corpus of real incidents, discriminates good reviewers from bad ones, and therefore can serve as a calibration regime for any architectural ruler. The null **H0** is that the metric does not discriminate — that radically different reviewers produce indistinguishable scores, or that a degenerate "flag everything" reviewer passes.

The experiment uses matched pairs derived from public postmortems: for each incident, a *failure case* (the pre-incident architecture, blinded against lexical and memorization cues) and a *healthy twin* (the same architecture with the mitigation present). Four reviewer conditions are tested, including two degenerate controls — an over-approver and an over-flagger — the latter being the decisive control, because a single-metric regime would pass it. Decision criteria are pre-registered. The protocol and a runnable skeleton are in `/experiments`. The cost is on the order of two days of corpus construction plus negligible API spend; a corroborating result is the central table of the eventual paper, and the corpus becomes the seed population of Layer 4.

## 5. Limitations

This is a position paper. The pipeline has not been deployed end-to-end at scale, the calibration experiment has not yet been run, and the related-work survey is targeted rather than systematic; adjacent efforts (notably Assurance 2.0 and DARPA ARCOS-style automated assurance, and unpublished industrial practice) may be closer than a few searches reveal. An empty space admits two readings — unseen, or attempted and found unworkable — and CAA's hardest risks are adoption (organizations buy rulers readily but resist being measured), corpus access (real incident data is proprietary and politically sensitive), and Goodhart effects on any reviewer-facing metric. These are named here so they can be tested rather than assumed away.

## References

Selected entry points (see links for full bibliographies):

- Asaadi, Denney, Menzies, Pai, Petroff. *Dynamic Assurance Cases: A Pathway to Trusted Autonomy.*
- *ACCESS: Assurance Case Centric Engineering of Safety-critical Systems.* arXiv:2403.15236.
- *Towards Continuous Assurance Case Creation for ADS with the Evidential Tool Bus.* arXiv:2403.01918.
- *Automatic instantiation of assurance cases from patterns using large language models.* Journal of Systems and Software, 2025.
- *Dynamic Safety Cases for Through-Life Safety Assurance* (DSC framework).
- *Towards Continuous Assurance with Formal Verification and Assurance Cases.* arXiv:2511.14805.
- Bloomfield & Rushby. *Assurance 2.0.* (assurance-case methodology — adjacent prior art to verify against.)

*This reference list is a starting point for a systematic review, not a complete bibliography. Contributions of prior art in the claimed intersection are explicitly invited.*
