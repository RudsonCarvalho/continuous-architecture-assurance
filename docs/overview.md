# Continuous Architecture Assurance (CAA)

### Calibrating AI reviewers as instruments — in one page

**Rudson Carvalho** · Independent Researcher

---

**The thesis, in one line:** CAA does not review your architecture. **CAA is the mechanism for measuring whether the things that review your architecture deserve to be trusted.**

**The problem.** Teams are starting to let AI review their architecture and code, and the reflex is to trust it — the model sounds competent, so its verdict is accepted. But an AI reviewer that has never been calibrated is not a reviewer; it is an opinion with a number on it. The market is full of "rulers" for judging software — well-architected frameworks, maturity models, checklists, AI reviewers — and nothing that tells you whether a ruler measures what it claims.

**The idea.** Treat an AI reviewer not as an oracle but as an **instrument to be calibrated**, the way a metrology lab calibrates a measuring device against a known standard. The standard is real incidents: does the reviewer catch the risk that actually caused a real outage (recall), and does it avoid crying wolf on a healthy system (false-positive rate)? The two numbers must be read as a pair — either alone is gameable. CAA is *ruler-agnostic*: your existing frameworks and reviewers plug in as instruments, provided they agree to be calibrated and to emit findings under a structured contract. The one rule that cannot be broken: the party that assures cannot be the party that produces.

**Does it work? The honest scorecard.** I built CAA and then spent five experimental attempts trying to *falsify* it, not confirm it. All numbers below are reconstructed from raw records:

| Claim | Status |
|---|---|
| Contract-bound review reduces false positives vs. naive review | **Demonstrated** (two independent corpora) |
| The paired recall/FP metric catches degenerate reviewers | **Demonstrated** |
| Recall discriminates among *plausible* reviewers | **Not demonstrated** (recall saturates on textual cases) |
| The metric catches a confident-misattribution reviewer | **Untested** (the control resisted three construction attempts) |
| A closed-rule automated assurance gate is sufficient on its own | **Refuted** (it failed in all five runs; only human audit caught each) |

That last row is the most important finding, and it arrived sideways: the automated gate I built to police the experiment accepted a serious defect *every single time*, and only an independent human reading the raw data caught it. For a framework whose entire pitch is "don't trust the reviewer, verify it," there is no more fitting result — the experiment proved its own founding rule.

**Scope, stated plainly.** This is a pilot. It establishes that a contract-bound reviewer can be calibrated against controlled *textual* incident pairs — not that CAA detects risk directly from live production systems, codebases, or telemetry. The honesty about where it does *not* work is the reason to trust where it does.

**When it is worth it.** Use CAA where AI participates in reviewing or operating systems and being *confidently wrong* is expensive — regulated, financial, high-stakes domains. Skip it where the stakes don't justify the overhead. Minimum adoption: plug *one* reviewer under contract into a process you already have, make it emit a structured verdict with traceable evidence, and measure it against a handful of your own real incidents.

---

### Go deeper

- **Understand the whole program** — the problem, the concepts, the full five-attempt saga, the verdict, and how to adopt it: **`docs/technical-report.md`**
- **The rigor** — three genre-separated papers (the framework, the pre-registered empirical study, the recursive gate-failure meta-paper): **`docs/papers/`**
- **The code, the corpus, the raw data** — reproducible, every number reconstructable independently of the harness: this repository.

*A pilot falsification report, honestly scoped — not a finished product. Which is exactly what the framework would require me to say.*

— *Rudson Carvalho, Independent Researcher*
