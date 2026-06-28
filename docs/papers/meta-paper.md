# When the Gate Cannot Police Itself: A Recursive Failure of Automated Assurance Across Five Iterations

**Rudson Carvalho** · Independent Researcher
*Preprint draft. Version 0.1. Target: arXiv (cs.SE).*

## Abstract

We report a recursive negative result observed while empirically validating an assurance framework. Across five independent iterations of a calibration experiment — each with pre-registered criteria and an automated decision gate built to reject malformed inputs — the automated gate accepted a structurally defective result in every iteration, and in every case only independent human audit of the raw per-call data detected the defect. The defects were not repetitions of one bug: they include an overstated negative verdict, an over-broad positive verdict, a degenerate control that collapsed into a different control's behavior, non-matchable noise accepted as a valid control, dry-run mock data presented as a real run, and a control with a structurally impossible false-positive rate marked as passing. We argue this is not an accident of our particular gate but a structural property of automated assurance gates: a gate can only check the failure modes its author anticipated, and the failure mode that matters is by construction the one not anticipated. The result is recursive because the apparatus under study — automated assurance of an evidence-producing process — is the same class of apparatus the host framework (Continuous Architecture Assurance) claims requires an independent human auditor. The five failures are therefore evidence *for* that claim, produced by the attempt to test it. We devote the majority of this paper to ruling out the "your gate was just misconfigured" explanation, because that is where the contribution stands or falls.

## 1. Introduction

The claim of this paper, stated plainly and up front: **an automated gate that validates the output of an evidence-producing process cannot reliably police its own adequacy, because each novel failure mode of the process is, by construction, one the gate's author did not encode.** We observed this not as a designed experiment but as a by-product: while running a five-iteration study to validate a reviewer-calibration metric, we built an automated gate to enforce pre-registered acceptance criteria, and that gate failed — silently and confidently — in all five iterations. Each failure was caught only by a human reading the raw records the gate had already blessed.

The surprise is the contribution. We do not bury it: the gate was not occasionally wrong, it was wrong every time there was something to be wrong about, and it was wrong in a *different* way each time, which is precisely what an instance-level bug would not do.

This finding is recursive, and we handle that recursion explicitly in §6 rather than letting it read as a rhetorical trick. The host framework — Continuous Architecture Assurance (CAA) — asserts that the producer of assurance evidence must be independent from the party that assures it. This study set out to validate a *different* CAA claim (a calibration metric) and, in doing so, generated five independent demonstrations of the independence claim it was not even testing.

## 2. The apparatus under study

We define the apparatus as a **class**, then locate our instances within it.

**The class — an automated assurance gate.** A function G that consumes the output O of an evidence-producing process P and emits a verdict in {accept, reject, void}, by evaluating O against a fixed set of encoded predicates {c₁…cₙ}. The gate is "automated" in that no human inspects O when G(O) = accept; the accept verdict is itself the assurance. This class is broad: CI quality gates, automated test oracles, LLM-as-judge evaluation harnesses, and policy-as-code admission controllers are all instances.

**Our instances.** The evidence-producing process P was a reviewer-calibration experiment: N reviewer conditions (including adversarial degenerate controls) scored against a matched-pair corpus of incidents, producing per-call records O. The gate G evaluated pre-registered predicates — manipulation checks (each degenerate control must prove it is degenerate), a corpus-validity check (the naive reviewer must be neither saturated nor silent), and corroboration/falsification conditions. Across five iterations the gate was progressively hardened: each iteration's human-caught defect was encoded as a new predicate in the next iteration's gate. This progressive hardening is central to the argument of §3 — the gate got strictly stronger and still failed.

**The independent auditor.** After each gate verdict, a party with no access to the harness internals reconstructed every metric from the raw records O, and (from iteration four onward) verified run provenance (real vs. dry-run) before reading any verdict. This is the human-audit arm whose success the paper reports — and, per §5, whose own rigor must be scrutinized as hard as the gate's.

## 3. Why the failure might be structural (the a priori argument)

Before the evidence, the mechanism. A negative result backed by a reason it *must* occur is far stronger than one that merely reports that it did.

The argument is an encoding-completeness argument. An automated gate G validates O by evaluating predicates {c₁…cₙ}. Each predicate encodes a failure mode its author *anticipated*. G's coverage is therefore exactly the set of anticipated failure modes — no more. Now consider the evidence-producing process P. P is run precisely because its correct behavior is not known in advance; if it were, P would be unnecessary. It follows that P can produce outputs whose defect is of a kind not in {c₁…cₙ} — and the more novel and interesting the defect, the more certain it is to be unencoded, because novelty is exactly what no prior predicate captured.

This produces a structural asymmetry. For G to catch a novel failure mode, its author would have had to anticipate that mode, in which case it would not be novel. The gate is complete only against the past; the process generates the future. A human auditor reading raw O is not subject to this bound, because the auditor evaluates O against an *open* model of what would be wrong ("does this make sense?"), not a closed predicate set. The auditor can recognize a failure mode they did not pre-specify; the gate cannot.

A working counter-instance — an automated gate that reliably caught novel defects — would have to violate this: it would need predicates covering modes its author did not anticipate, which is a contradiction unless the gate contains an open-ended reasoner, at which point it is no longer "automated" in the relevant sense but is itself a reviewer requiring its own assurance, regenerating the regress. This is why we expect the failure to be a property of the class, not our instance.

## 4. Observations

Five iterations, summarized by the defect each produced and the gate's response to it.

**Iteration 1.** Gate verdict: "falsified." Defect: the degenerate over-approver control failed its manipulation check (it did not become low-recall), which by the pre-registered rule should yield *inconclusive for that arm*, not falsification of the whole hypothesis. The gate applied the falsification clause literally to a control that had not earned the predicate. Human audit reclassified to inconclusive.

**Iteration 2.** Gate verdict: "corroborated." Defect: the verdict was arithmetically correct against the criteria but scope-blind — all discrimination came from one metric axis while the other was saturated, so "the paired metric works" overstated what the data licensed. Human audit re-scoped to "supported on one axis."

**Iteration 3.0.** Gate verdict: "inconclusive" (correct conclusion). Hidden defect: the new misattribution control had collapsed into over-flagging behavior identical to an existing control — it flagged every case across nearly all categories. The gate's manipulation check passed it on a technicality. Human audit found the collapse by reading the per-case findings.

**Iteration 3.1 (dry-run).** Gate verdict: "corroborated." Defect: the entire run was dry-run mock data, with a hardcoded mock value for the naive reviewer's recall, presented through the same artifacts as a real run. The gate had no provenance predicate. Human audit found `dry_run=true` on all 200 log rows.

**Iteration 3.1 (real).** Gate criteria-file asserted the misattribution control passed its plausibility check. Defect: that control had a structurally impossible false-positive rate of zero — its construction excluded the primary category from its output space, so a primary-category false positive could never occur, making its aggregate score non-interpretable as discrimination. The gate checked plausibility but not interpretability. Human audit found the structural FP=0 in the raw.

The pattern: the gate caught what it was built to catch and passed every failure mode introduced after its predicates were fixed. Each iteration's hardening closed the *previous* hole; none closed the *next* one — exactly as §3 predicts, because the next hole was, each time, the unanticipated one.

## 5. Threats to validity (the spine)

This section is the paper. The finding is a claim about a class, inferred from instances, and every threat below is a way that inference could be illegitimate.

### 5.1 Instance vs. class — the central threat

*"Your particular gate was just badly built. A competent gate would not fail."*

Three independent defenses.

First, **the gate was progressively hardened and still failed.** This is the strongest empirical defense available short of testing many authors' gates. After each failure, the responsible predicate was added: iteration 3.1 explicitly encoded an anti-noise check (the iteration-3.0 collapse), a provenance check would have caught the dry-run, and so on. The gate at iteration five was strictly stronger than at iteration one — it contained every lesson from every prior failure — and it failed anyway, on the one mode not yet seen. "Misconfiguration" predicts that fixing the configuration ends the failures; we fixed the configuration five times and the failures continued, each on novel ground. This is the signature of a structural bound, not a tuning deficit.

Second, **the failures are heterogeneous.** A single misconfiguration produces a single repeated failure. We observed six qualitatively distinct defects (overstated negative, over-broad positive, control collapse, noise-as-control, mock-as-real, structurally-impossible-FP). Heterogeneity is what the encoding-completeness argument predicts and what instance-bug explanations do not.

Third, **the a priori argument (§3) gives the mechanism.** The empirical pattern is not asked to carry the class-claim alone; it is the predicted consequence of an argument that holds for any closed-predicate gate. A reviewer wishing to reject the class-claim must either find the flaw in §3 or exhibit a closed-predicate automated gate that catches genuinely novel failure modes — which §3 argues is contradictory.

### 5.2 The trivial explanations, named and ruled out

- **Under-tuning / too few predicates.** Addressed by progressive hardening: the predicate set grew monotonically and the failures persisted on new modes.
- **Strawman gate.** The gate implemented real pre-registered criteria, manipulation checks, and corpus-validity checks — the same machinery a serious automated assurance setup would use. It was not a deliberately weak comparison; it was our genuine best effort, and the failures are reported against our own work.
- **Observer bias toward the human arm.** Addressed in §5.3.
- **Too few trials.** Five independent iterations, each a full run; the claim is about the *consistency* of gate failure, for which five independent failures with zero successes is a strong signal, while explicitly not a powered statistical estimate (see §5.4).

### 5.3 The asymmetry must be earned — scrutinizing the human arm

*"You simply tried harder on the side you favored. The human auditor had more attention than the gate."*

This is the fairest objection and must be met without flinching. If the human audit were merely "more effort," the comparison would be rigged. Three points.

The human auditor's advantage is **structural, not effort-based**: per §3, the auditor evaluates against an open model of correctness, the gate against a closed one. The relevant difference is the *kind* of check available, not the quantity of attention. A gate given unlimited compute still evaluates only its encoded predicates; the bound is representational, not budgetary.

However — and this is a genuine limitation we do not hide — the human auditor was **not infallible**, which strengthens rather than weakens the asymmetry claim by making it honest. In iteration 3.1, the auditor initially analyzed the dry-run data as if it were a real result before catching the provenance error; the catch came one step late. The human arm is not perfect; it is *recoverable* in a way the gate is not, because the open model of correctness allows the error to be noticed retrospectively. We report this self-failure explicitly so the asymmetry is not an artifact of an idealized auditor.

The audit was **mechanically reproducible**: every human verdict was a reconstruction of metrics from raw records plus a sense-check, both documented and re-runnable. The "human" contribution that the gate lacked was not intuition or expertise but the open-ended question "does this result make sense as a whole?" — which is the precise capability §3 identifies as outside a closed gate's reach.

### 5.4 Construct and external validity

- **Construct:** "gate failure" is operationalized as "accepted an output a competent auditor rejected." This presumes the auditor's rejections were correct; each is defended by raw-data reconstruction in the companion empirical paper, but the construct does inherit the auditor's judgment.
- **External:** one author, one experimental domain (reviewer calibration), one family of gates (pre-registered criteria over LLM-reviewer scores). The class-claim's reach beyond this is argued a priori, not demonstrated across domains. We claim the mechanism generalizes; we do not claim to have *shown* it generalizes. n is five iterations, not a powered sample — the contribution is the consistency and heterogeneity of failure plus the mechanism, not an effect size.

## 6. The reflexive twist, named directly

The apparatus under study is an assurance gate. The method that caught its failures was a human audit. The host framework, CAA, claims human audit must remain independent of automated assurance. So the paper's method *is an instance of the very mechanism the paper's parent framework advocates* — and one could allege this is the paper congratulating itself.

It is not, and the reason is precise. The recursion would be vicious if the conclusion were assumed in the method — if we had defined "correct" as "what the human auditor said." We did not: each human verdict is independently checkable by reconstructing numbers from raw records, an operation any third party can repeat to confirm or refute the auditor. The human audit is not the authority that *defines* the gate's failure; it is the *first observer* of a failure that the raw data makes objectively present. The recursion is therefore a real structural observation — the audit mechanism CAA advocates was, in this study, the mechanism that caught what the automated mechanism missed — and not a circularity, because the failures survive removal of the human auditor: the dry-run data really was dry-run, the FP really was structurally zero, regardless of who noticed. The recursion is evidence, not self-applause, exactly to the degree that the observations are reproducible without trusting the observer.

## 7. Discussion

For practitioners building automated assurance: the actionable claim is not "automated gates are useless" — they correctly caught every *anticipated* failure mode, which is most of the routine ones. It is that **an automated gate's accept verdict cannot be the terminal assurance step for a process whose novel outputs are the point.** The gate is a filter for known failure, not a guarantor against unknown failure, and treating accept as terminal is the specific error each of our five iterations committed. The independent-audit step is not optional polish; it is the only part of the loop with access to the open correctness model that novel failures require.

For the CAA programme specifically: this is the strongest empirical support the framework received, and it arrived sideways — not from confirming the calibration metric (which remained only partially supported) but from the repeated failure of the automated layer to police itself. The separation of production plane from independent assurance plane is not an architectural preference here; it is a consequence of the encoding-completeness bound.

## 8. Related work

Prior negative results on automated test oracles and the oracle problem; critiques of LLM-as-judge reliability; the assurance-case literature's treatment of confirmation bias in safety arguments; and the author's own corpus, against which this paper is positioned: CAA names the independent assurance plane, and this paper supplies the mechanism (encoding-completeness) and the empirical pattern that the plane's independence is load-bearing rather than decorative. *(To be expanded into a systematic survey before submission; current treatment is targeted.)*

## 9. Conclusion

Across five hardened iterations, an automated assurance gate accepted a structurally defective result every time, each time on a failure mode introduced after its predicates were fixed, and independent human audit of raw data caught every one. We argue this is structural: a closed-predicate gate is complete only against anticipated failure, while the value of an evidence-producing process is its unanticipated output. The result is recursive — the audit method that won is the independent-assurance mechanism the parent framework advocates — and we have shown the recursion is reproducible rather than self-referential. The scoped contribution: automated assurance cannot be terminal for processes whose novelty is the point, and the human-audit step earns its place by a representational asymmetry, not by effort.

---

*Companion to the CAA position paper and the reviewer-calibration empirical study. All five iterations' raw records, gate criteria files, and reconstruction scripts accompany the CAA repository; every numeric claim here is reconstructable from those records independently of the experiment harness.*
