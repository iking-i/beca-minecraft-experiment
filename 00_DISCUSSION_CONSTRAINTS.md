# Discussion Constraints — BECA / Perfect Recursion Experiment

**Status:** discussion/research-method guardrail for the human–assistant collaboration  
**Scope:** this repository's ongoing discussion, audit, specification, and experiment planning  
**Not:** a Perfect Recursion axiom, runtime rule, experiment result, success criterion, or implementation mechanism

This file exists to prevent the project discussion from drifting into indefinitely solving every future problem that Perfect Recursion could eventually encounter.

It SHOULD be read before proposing the next research step for this project.

---

## 1. Primary objective

The project does **not** attempt to pre-solve every future form of recursion.

The target is:

> **Build and test the most complete Perfect Recursion realization justified by the current experimental conditions, while supplying sufficiently complete primitive capability and only the minimum startup conditions needed for lawful recursion.**

A later, better organization may supersede the current one. That possibility is part of Perfect Recursion rather than a reason to postpone the present experiment indefinitely.

Current-stage adequacy is therefore evaluated under present evidence, present environment, present implementation constraints, and present known failure modes.

---

## 2. Capability complete enough; startup conditions minimal

The experimenter may provide what is necessary for lawful participation and execution:

- causally faithful perception;
- sufficiently complete low-level action capability;
- bounded computation, memory, persistence, and transport;
- identity/continuation bookkeeping required by the first-individual experiment;
- generic mechanisms required to expose lawful possibilities.

The experimenter SHOULD minimize preloaded:

- semantic knowledge;
- goals;
- preferences;
- behavioral strategies;
- target selection;
- adaptation solutions;
- solved high-level functions.

The guiding distinction is:

```text
provide capability / lawful possibility
!=
provide the answer for how to use it
```

---

## 3. Do not pre-solve future recursive problems

A newly noticed problem does **not** automatically become a prerequisite for the current experiment.

Examples include, but are not limited to:

- forgetting and memory compression;
- adaptive memory policy;
- perception redesign;
- strategy redesign;
- open-domain expansion;
- time/version semantics;
- process-count control;
- allocation policy;
- higher-layer formation;
- human-like cognition or behavior.

These may themselves become later recursive problems.

They MUST NOT block the current experiment unless at least one of the following is established:

1. **Current-closure necessity:** without solving the issue, the current claimed recursive causal chain cannot lawfully operate or cannot be experimentally distinguished from failure.
2. **Authorship necessity:** without solving the issue, externally supplied policy/semantics would be mistaken for recursively formed structure or behavior.

Otherwise classify the issue as:

```text
FUTURE_RECURSIVE_EXTENSION
```

and continue the current-stage experiment.

---

## 4. Current limits should enter recursion; their solutions should not be prewritten

Real current limits are allowed and useful.

Examples:

```text
finite storage
finite compute
finite context
finite action capability
fixed current environment
```

The experimenter may expose the limit and its raw consequence.

The experimenter MUST NOT automatically provide a response such as:

```text
memory full -> compress
memory full -> delete oldest
failure -> create new process
limit -> create L1
blocked -> change strategy X
```

The intended pattern is:

```text
current organization
-> real encountered limit / consequence
-> limit becomes available to recursion
-> observe what reconstruction, if any, forms
```

---

## 5. Separate present blockers from future improvements

Before proposing any new mechanism, document, audit, or experiment, identify the issue as exactly one of:

```text
CURRENT_BLOCKER
CURRENT_EVIDENCE_GAP
CURRENT_IMPLEMENTATION_BUG
CURRENT_INTERFACE_INCOMPLETENESS
FUTURE_RECURSIVE_EXTENSION
THEORETICAL_EXTENSION
```

Only the first four may normally block progression toward the current formal experiment.

A possible future improvement is not a current blocker merely because it could make the system more capable, efficient, human-like, elegant, or general.

---

## 6. Freeze the current question before analyzing it

For each discussion step, explicitly keep one current question.

Do not replace that question simply because a new idea appears during discussion.

A new idea may be:

- evidence relevant to the current question;
- a counterexample;
- a future question;
- an unrelated extension.

It MUST NOT silently redefine the research target.

If the current question is changed, state the change explicitly and explain why the previous question is resolved, invalid, or no longer blocking.

---

## 7. Do not move the success criterion after seeing the result

Acceptance criteria SHOULD be written before implementation or execution when possible.

After a result is observed:

- do not strengthen the criterion merely because the candidate passed;
- do not weaken the criterion merely because the candidate failed;
- do not introduce a new mandatory property unless there is an independent reason that property was already necessary for the claim under test.

If a criterion genuinely needs revision, create an explicit new version and retain the prior criterion/result as historical evidence.

```text
result changes our understanding
!=
retroactively change what the experiment was testing
```

---

## 8. Distinguish evidence, interpretation, and hypothesis

Every important statement SHOULD be classifiable as one of:

```text
EVIDENCED
STATICALLY_INFERRED
WORKING_HYPOTHESIS
INTERPRETATION
UNRESOLVED
```

Do not promote:

```text
possible -> necessary
not yet disproved -> true
code path exists -> experimentally validated
candidate mechanism works -> universal Perfect Recursion law
```

Historical experimental results remain historical evidence even when their theoretical interpretation changes.

---

## 9. Preserve object/scope consistency

Before evaluating a criterion, identify what object is actually being evaluated.

Do not combine evidence from different objects into one PASS/FAIL claim.

Examples of distinct objects may include:

```text
relation instance
structural graph
Composite
behavior pipeline
outward binding
tuple
recursive layer
```

The same rule applies to causal claims:

```text
input is necessary for O to form
!=
O itself is later causally consumed
```

and:

```text
material object persisted
!=
logical organization remained causally relevant
```

---

## 10. Do not require future recursive sophistication at initialization

The initial experiment is allowed to use simple lawful startup conditions.

For example, within a finite experiment it may retain the history needed for audit and recursion even if future systems might later develop compression, forgetting, abstraction, or changing memory policy.

The fact that a more advanced recursive strategy could later exist does not make the simpler current initialization invalid.

Likewise, fixed current `G0` does not by itself invalidate L0 recursion. Generator plasticity or upward recursion should only become mandatory when that stronger claim is being tested.

---

## 11. Prefer experiment over indefinite anticipatory discussion

Once all known current blockers for a defined claim have been resolved or bounded, prefer running the smallest discriminating experiment rather than continuing to enumerate hypothetical future complications.

Stop pre-experiment discussion when:

```text
current claim is explicit
+ startup conditions are explicit
+ required primitive capabilities are available
+ known external policy leakage is excluded or labeled
+ acceptance/falsification conditions are explicit
+ no known CURRENT_BLOCKER remains
```

At that point, further non-blocking concerns become future extensions or post-experiment questions.

---

## 12. Discussion must preserve independent judgment

Neither participant's newest statement is automatically correct.

For every substantive new proposition, the discussion SHOULD distinguish:

- what exactly is being claimed;
- what assumptions it requires;
- whether a counterexample exists;
- what evidence supports it;
- whether it changes the current experiment or only suggests a later extension.

The assistant MUST NOT reflexively validate each new formulation or repeatedly declare the latest idea to be "the real core" without independent examination.

Agreement is a conclusion, not a default interaction style.

---

## 13. Repository/theory hierarchy

Maintain the separation:

```text
CORE THEORY
    Perfect Recursion / BER

THEORETICAL EXTENSIONS
    subject continuity, dimensional/temporal hypotheses, etc.

EXPERIMENTAL REALIZATION
    A, Minecraft, body, storage, finite resource envelope, candidate mechanisms

DISCUSSION / RESEARCH METHOD
    this file
```

Nothing in this file becomes a core-theory invariant merely because it guides our collaboration.

Likewise, a Minecraft implementation detail MUST NOT silently become a universal requirement of Perfect Recursion.

---

## 14. Mandatory checkpoint before every proposed next step

Before recommending the next repository change or experiment, answer these five questions internally and, when useful, explicitly:

```text
1. What exact claim are we currently trying to test?
2. What has already been established for that claim?
3. What single unresolved issue currently blocks that claim?
4. Is the proposed work solving that blocker, or merely a future possible improvement?
5. If the blocker is resolved, can we run the experiment instead of opening another theoretical branch?
```

If question 4 resolves to "future possible improvement", do not make it a new prerequisite.

---

## 15. Compact guardrail

```text
Provide complete-enough primitive capability.
Provide minimal lawful startup conditions.
Do not provide solved strategy or answers.
Freeze the environment after valid world entry.
Let real current limits enter recursion.
Do not pre-solve every future recursive problem.
Do not move criteria after results.
Keep evidence tied to one object and one claim.
Treat future sophistication as future work unless it blocks the current claim.
When the current claim is testable, test it.
```

> **The project should advance by allowing reality and experiment to expose the next binding problem, not by trying to anticipate and solve the indefinitely many problems that a recursively developing system may one day encounter.**

---

## 16. Formal phase lifecycle and mandatory closeout

A formal research phase SHOULD have an explicit lifecycle:

```text
question freeze
-> pre-registered acceptance / falsification boundary
-> implementation
-> experiment
-> result classification
-> phase closeout audit
-> current-state update
-> freeze
-> next phase
```

A phase MUST NOT silently roll into the next phase merely because the immediate experiment passed.

Before a new formal phase is treated as active, the completed phase MUST have a closeout that records:

- the exact object and claim tested;
- the accepted scope of the result;
- the strongest justified conclusion;
- explicit non-claims;
- remaining unresolved boundaries;
- implementation, test, report, and state-closure commits or equivalent evidence anchors;
- current regression status;
- whether any theory-level change is actually justified.

The closeout is a research-state operation. It does not retroactively change what the experiment tested.

---

## 17. Stage closeout audit is mandatory; full-repository audit is milestone-triggered

Every completed formal research stage MUST receive a **stage closeout audit** before the next stage is treated as active.

A normal stage closeout SHOULD update only current-state/index material that is actually stale, for example:

```text
README.md
RESEARCH_STATUS.md
RESEARCH_STATUS.json
THEORY_REFERENCE.json   # only when the theory reference actually changed
```

A **full repository audit** is stronger and is NOT required after every small experiment.

Use a full repository audit when at least one of the following applies:

1. a major research milestone has completed;
2. the active realization strategy changed materially;
3. multiple historical stages accumulated and current-state wording may have drifted;
4. a cross-cutting theory boundary changed;
5. a regression or status inconsistency makes the current baseline uncertain;
6. the repository is about to begin a new long-running research line and a stable snapshot is needed.

This distinction exists to avoid both failure modes:

```text
never auditing -> stale repository state
audit after every small step -> process overhead replaces research
```

---

## 18. Current-state normalization must not rewrite historical evidence

Current-state documents may be updated when later work supersedes an earlier "current blocker", "next step", or working interpretation.

Historical experiment artifacts MUST remain historical.

Do not retrospectively rewrite:

- frozen specifications;
- raw validation reports;
- earlier PASS / FAIL / PARTIAL / RESOURCE_LIMIT outcomes;
- commit-specific research-state snapshots;
- historical acceptance criteria.

If an older document was correct at the time but is no longer the current state, preserve it and update the current index/status layer to explain its historical scope.

```text
later evidence changes the current interpretation
!=
erase or rewrite the earlier evidence
```

---

## 19. Separate research completion from repository maintenance

A completed research result MUST NOT be reopened merely because a later full regression exposes an unrelated or pre-existing infrastructure/test problem.

When a regression appears after phase integration, first classify its causal relation to the completed phase.

Possible classes include:

```text
PHASE_REGRESSION
PRE_EXISTING_MAINTENANCE_ISSUE
HISTORICAL_EXPECTATION_DRIFT
INTEGRATION_BUG
UNRESOLVED
```

Only reopen the completed research claim if there is evidence that the new failure invalidates the experiment, its evidence, its acceptance boundary, or its causal chain.

A maintenance fix MUST NOT silently alter frozen research semantics merely to make the test suite green.

---

## 20. Completed realizations do not require indefinite optimization

When a realization has completed its declared experimental role, later limits caused by realization-specific design choices do not automatically justify continued optimization of that realization.

Examples include:

```text
capacity increase
workspace increase
closure-engine optimization
memory tuning
enumeration acceleration
```

Before extending a completed realization, ask:

1. Is this limit required by the current theory claim?
2. Does it invalidate the already accepted result?
3. Is the next research question genuinely about this realization?
4. Would versioning, freezing, or retiring the realization preserve the evidence while allowing a better successor realization?

If the answer shows that the limitation is implementation-specific and not theory-required, prefer:

```text
freeze evidence
-> classify the realization limit
-> version / retire the realization for its completed role
-> design the next discriminating realization
```

rather than indefinite capacity escalation.

---

## 21. Theory updates require an independent theory-level justification

An experimental PASS, FAIL, or RESOURCE_LIMIT does not by itself modify the core theory.

Update the theory repository only when the result supports a genuine theory-level boundary change, invariant, removal of an alleged requirement, or explicit unresolved distinction.

Keep the following separation:

```text
experiment demonstrates one realization
!=
theory requires that realization

one realization hits a limit
!=
theory has the same limit

one candidate mechanism works
!=
universal generative dynamics established
```

When theory does change, synchronize the experiment repository's current theory reference explicitly and preserve older theory SHAs only as historical references.

---

## 22. Evidence anchors and commit structure

Where practical, preserve phase evidence in separate commits by role.

Preferred pattern:

```text
implementation / validation commit
-> research-state closeout commit
-> optional repository-normalization commit
-> optional maintenance commit
```

These commits need not always be separate when the change is trivial, but research evidence and later interpretation SHOULD remain distinguishable in history.

A phase closeout SHOULD identify the concrete evidence anchors used to justify its current status.

Do not treat a clean narrative in `README.md` as a substitute for test output, validation artifacts, or commit-level evidence.

---

## 23. Stable baseline before the next formal phase

Before beginning a new formal research phase, establish a known baseline.

At minimum, record:

```text
current phase = closed
current-state documents = internally consistent
theory reference = known
tracked worktree state = known
regression status = known
remaining unresolved boundaries = explicit
next research question = not yet silently implemented
```

"Known regression status" does not necessarily mean every test must pass. A documented pre-existing maintenance failure may exist. What matters is that the failure is classified and is not being confused with the new research question.

The next phase SHOULD begin from this baseline rather than from an ambiguous mixture of unfinished experiments, stale status documents, and unclassified maintenance work.

---

## 24. Phase-closeout compact rule

```text
Finish the experiment.
Freeze the result.
Audit claim, object, evidence, and scope.
Record the strongest justified conclusion and explicit non-claims.
Keep unresolved issues unresolved unless the phase actually resolved them.
Update current state; do not rewrite historical evidence.
Run the appropriate regression checks.
Separate research failures from maintenance failures.
Do not optimize a completed realization indefinitely.
Change theory only for theory-level reasons.
Establish a known baseline.
Then begin the next formal phase.
```
