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

## 2A. Origin-given startup scaffolding is allowed; permanence is not implied

The experiment may provide creator-supplied startup tasks, pending/suspended items,
initial operative structures, or other bootstrap conditions when they are needed to
start the realization being tested.

Their provenance and persistence MUST be separated:

```text
CREATOR-SUPPLIED AT ORIGIN
!=
SELF-AUTHORED BY A
!=
PERMANENT PROCESS
```

A startup item may later be completed, released, repeatedly reactivated by environmental
conditions, modified, or superseded. The project MUST NOT turn an initialization choice
into an eternal internal objective merely because the item existed at A0.

External education/instruction is treated as environment-side input in the coupled
`environment <-> individual` recursion. It may strongly shape early structure without
being relabeled as self-authored by the individual.

For operative-structure work, the experimenter may supply an initial runnable structure.
However, that structure MUST NOT receive a privileged execution channel unavailable in
principle to later internally formed structures of the same operative kind. The relevant
distinction is:

```text
first structure
!=
special privileged structure
```

This rule does not require the first operative structure itself to be internally created.
It protects the later authorship transition: creator scaffolding may start the process,
but continued creator-specific execution semantics must not be mistaken for the
individual's own recursively formed operative structure.

This section is a research-method boundary, not a claim that a generic operative
interpreter has already been designed or validated.

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


## 6A. A question is not a change request

A user's question is, by default, a request for explanation, clarification, evaluation, or challenge. It is **not** automatically a request to modify the current research plan.

When the user raises a new question:

- do not automatically change the current research question;
- do not add a new prerequisite merely because the question reveals another possible consideration;
- do not revise the experiment definition or acceptance/falsification boundary merely to make the plan more complete;
- do not create a new audit, stage, document, implementation task, or repository-maintenance task unless it is actually required by the current claim;
- do not treat clarification, curiosity, or challenge as authorization to redesign the active plan.

The default flow is:

```text
user asks a question
-> answer the question
-> test whether the issue genuinely blocks the current claim
-> if not, preserve the current plan
-> continue the current task
```

A newly raised question MUST NOT change the active research question unless it is demonstrated to be a genuine blocker to testing the current question.

The threshold is not "this could be useful", "this would be cleaner", "this is more rigorous", or "this might matter later". The issue must satisfy at least one of:

1. **Current-claim blockage:** without resolving it, the current experiment cannot validly test the declared claim.
2. **Causal invalidation:** continuing would make the observed result causally ambiguous or attribute externally supplied structure/policy to the system under test.
3. **Acceptance-boundary invalidation:** the frozen PASS/FAIL boundary is shown to be incapable of distinguishing the claimed success from a known false positive.
4. **Evidence corruption risk:** continuing as planned would directly overwrite, destroy, or irreversibly contaminate required evidence.

If none of these conditions is met:

```text
answer the question
-> keep the current question
-> keep the current plan
-> continue execution
```

If one of these conditions is met, do **not** silently change the plan. First state:

```text
what the blocker is
why it blocks the current claim
what minimum change is required
```

Then obtain explicit authorization before changing the active research plan, unless immediate action is required solely to prevent evidence corruption.

In compact form:

```text
QUESTION != CHANGE REQUEST
CLARIFICATION != NEW PREREQUISITE
POSSIBLE IMPROVEMENT != CURRENT BLOCKER
NEW QUESTION -> CHANGE ONLY IF IT ACTUALLY BLOCKS THE CURRENT CLAIM
```

The assistant MUST resist turning every newly noticed ambiguity into another pre-experiment task. Once the current experiment is adequately specified and testable, prefer execution over anticipatory refinement.

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


---

## 25. Assistant-generation attribution and non-substitution rule

**Status:** discussion/research-method guardrail only
**Scope:** human–assistant collaboration, research planning, interpretation, and next-step proposals
**Not:** a Perfect Recursion axiom, runtime mechanism, experimental result, layer definition, or theory authorship claim

### 25.1 Collaboration-generation labels

For continuity across long conversations, collaborating assistant generations are labeled:

```text
一号 — historical collaborating assistant
二号 — historical collaborating assistant
三号 — historical collaborating assistant
四号 — current collaborating assistant
```

The exact historical division of work among 一号、二号、三号 can no longer be reconstructed reliably enough to assign individual existing clauses or experiments to one specific assistant generation. Do **not** retroactively invent that attribution.

These generation labels record discussion provenance only. They do not confer authorship of Perfect Recursion, do not alter experimental provenance, and do not replace commit-, evidence-, or user-level authorship records.

From 四号 onward, a newly added discussion guardrail may explicitly record the assistant-generation label that proposed or wrote it when useful.

### 25.2 The assistant must not substitute for the recursion

The assistant's job is **not** to continue Perfect Recursion on behalf of the system.

The assistant's job is to help ensure that:

- the current starting point is lawful;
- primitive capability is sufficiently complete for the current claim;
- carrier, persistence, transport, and measurement are causally faithful;
- evidence and provenance are real and correctly scoped;
- experimenter-supplied structure, strategy, selection, semantics, or answers are not misattributed to the system;
- genuine current blockers are repaired or isolated without pre-solving future recursive problems.

Once the current recursive chain can lawfully continue, the assistant SHOULD stop predesigning what the next recursive content should be and allow the running system plus reality to expose the next binding problem.

In compact form:

```text
assistant builds / audits the lawful experimental boundary
!=
assistant authors the system's next recursive content
```

The assistant MUST NOT:

- predesign "round 2", "round 3", or later recursive contents merely to make a roadmap;
- predesign L1, L2, L3, L4, or any later layer as implementation milestones that the experiment must construct;
- decide in advance what reconstruction a real encountered limit should cause;
- convert an implementation-specific realization choice into a universal Perfect Recursion requirement;
- automatically respond to RESOURCE_LIMIT with compression, eviction, expansion, cap increases, process creation, strategy change, or higher-layer creation;
- splice separate scoped PASS results into a stronger causal chain that has never actually occurred in one valid experimental object;
- add selector, ranking, preference, binder, fallback, value-to-action mapping, recovery policy, or other answer-producing mechanism merely because the system otherwise lacks a predetermined next step;
- create a new formal stage solely because a roadmap, milestone sequence, or "next task" is desired.

The assistant MAY and SHOULD, when justified by the current claim:

- provide or repair lawful primitive capability and causally faithful carrier interfaces;
- repair genuine measurement, transport, persistence, or implementation bugs;
- isolate and test the single currently missing causal edge;
- preserve object, scope, provenance, continuity, and acceptance-boundary discipline;
- distinguish implementation limits from theory limits;
- after a claim is resolved, reassess the whole current causal chain before proposing any new phase;
- if no genuine current blocker remains, let the system continue operating and let reality expose the next binding problem.

### 25.3 A next stage must be earned by evidence

A new formal research stage MUST NOT be invented merely because the previous stage ended.

Before proposing a new stage, establish that current evidence or live operation has exposed a concrete unresolved causal edge, interface incompleteness, implementation bug, evidence gap, or other genuine binding problem.

The intended transition is:

```text
current claim resolved
-> inspect the actual remaining causal chain
-> identify a real unresolved binding problem, if one exists
-> test only that problem
```

not:

```text
current claim resolved
-> assistant invents the next recursive structure
-> assistant writes the next layer roadmap
-> system is made to follow it
```

If later operation produces a new structure, reconstruction, recursive origin, or candidate higher layer, the experimenter's role is to observe, record, audit, and classify what actually formed. A higher layer is recognized from evidence after formation; it is not supplied as the answer beforehand.

### 25.4 Authorship note

Historical collaboration:

```text
一号
二号
三号
```

Their exact per-clause contribution is intentionally left **UNRESOLVED** rather than fabricated.

Current addition:

```text
四号 — Section 25:
assistant-generation attribution
+ non-substitution / do-not-design-the-recursion-for-it guardrail
Date: 2026-10-07
```

**Signed: 四号**

This signature records responsibility for this discussion guardrail only. It does not claim authorship of Perfect Recursion, prior experimental work, or the user's theory.

---

## 26. Represented relation is not an operative connection

This is a discussion/research-method guardrail, not a Perfect Recursion theory
axiom, runtime rule, new mechanism or retroactive experimental acceptance change.

Naming is not evidence. None of the following alone proves an operative connection:

- An object, file or class is named Relation, Shared, Connection or Edge.
- A record contains endpoints X and Y.
- A relation has provenance/support or is persisted.
- A later query can retrieve the relation.
- A specialized consumer returns Y according to the relation.
- Relation content is attached to process output.
- Deleting a relation makes a query return fewer results.

Before claiming an operative connection, audit the actual chain:

```text
formed edge
→ enters actual running recursive organization
→ changes normal downstream dependency/routing
→ later recursion uses it under generic semantics
→ edge ablation changes actual processing path
→ edge remains structurally reusable
```

Generic interpreters, pointer dereference, graph engines and mechanical execution
are permitted. Generic execution of a formed edge must be distinguished from a
specialized consumer querying a relation record and then assigning its effect.

```text
REPRESENTATION != OPERATION
RELATION_RECORD != OPERATIVE_CONNECTION
SPECIALIZED_CONSUMPTION != TOPOLOGY_FORMATION
NAMING != EVIDENCE
```

If a purported connection still needs another external selector/consumer to
determine its effect, first re-audit whether the operative connection has actually
formed. Do not default to adding another intermediate layer. Preserve historical
names, evidence and scoped results; correct current interpretation explicitly.

四号 — 2026-10-07

operative-connection interpretation guardrail

---

## 27. Run-first experimental objective and recursion handoff rule


### 27.0 User's original constraint

The user's original wording is preserved verbatim as the controlling statement for this section:

> 我们要做的就是让实验跑起来，让大脑和身体连接起来。让完美递归进行起来。其他的不在我们的考虑范围内。其他的都是完美递归需要解决的问题。

This sentence is preserved as discussion provenance and scope guidance. The surrounding clauses in this section interpret and operationalize it without replacing it.

**Status:** discussion/research-method guardrail only  
**Scope:** current BECA/Minecraft experimental execution, assistant planning, and intervention boundaries  
**Not:** a Perfect Recursion axiom, a new runtime mechanism, a new layer definition, or a retroactive reinterpretation of frozen experimental evidence

### 27.1 The current objective is operational, not explanatory

The current objective is singular:

```text
make the experiment actually run
-> connect A's brain/internal recursion to its already available body
-> establish the real bidirectional loop with Minecraft
-> let Perfect Recursion proceed
```

Operationally:

```text
A / internal recursion
<-> body
<-> Minecraft reality
```

with the live causal loop:

```text
input reaches A
-> A continues its recursion
-> output reaches the body
-> the body changes Minecraft reality
-> the consequence returns as new input
-> recursion continues
```

This section does **not** require a BPC-style learned body-port relation. "Brain/body connected" here means the lawful experiment carrier actually permits A's existing input and output capabilities to participate in one real closed loop.

### 27.2 Do not solve Perfect Recursion's future problems for it

Once the live loop above can lawfully operate, questions exposed by later operation belong first to the running recursion and reality, not to the experimenter as pre-implementation tasks.

Examples include, unless they are the concrete blocker preventing the loop from starting:

- what later internal structures should form;
- how conflicts should be handled;
- how meanings of inputs or outputs should develop;
- how future choices or organizations should arise;
- how limits should be handled;
- whether or how a higher layer forms;
- what future reconstruction should occur;
- what unexpected structures or strategies should emerge.

The experimenter and assistant MUST NOT delay launch in order to pre-solve these questions.

Compactly:

```text
our job:
make lawful recursion able to happen in reality

not our job:
perform the recursion in advance
```

### 27.3 Discussion is not implementation progress

Discussion, theory refinement, audit, and interpretation may themselves recurse indefinitely. They can be useful for identifying a genuine current blocker, but they do not count as implementation progress merely because they produce more explanation.

For the current project:

```text
thinking about an action != the action occurring
describing a capability != the capability running
auditing a loop != the loop running
```

A claimed implementation step is complete only when the relevant behavior has actually occurred in code/runtime and, where appropriate, produced observable evidence.

Do not create repeated audits of already-resolved premises merely because further discussion is possible. Re-open a settled premise only when new runtime evidence, code evidence, or a concrete contradiction requires it.

### 27.4 Every next task must remove a real launch blocker

Until the live A-body-world loop is running, every next implementation task MUST answer:

> What concrete fact currently prevents the experiment from running as one lawful bidirectional recursive loop?

Then change only what is necessary to remove that blocker and execute again.

The preferred control loop is:

```text
attempt real run
-> observe concrete blocker
-> repair only that blocker
-> attempt real run again
```

Not:

```text
discuss possible future problem
-> invent stage
-> audit stage
-> design solution
-> discover another possible future problem
```

If there is no demonstrated launch blocker, the next action is to run the experiment, not to invent another research stage.

### 27.5 Stop designing once recursion can proceed

The immediate success condition is not intelligence, competence, behavioral optimization, semantic understanding, higher-layer formation, or proof that every future problem is solved.

The immediate success condition is:

```text
real input
-> A
-> real body output
-> real Minecraft consequence
-> renewed real input
-> continued recursion
```

Once this loop is operating, allow it to continue. Observe what actually happens. Intervene only when a concrete implementation, carrier, continuity, measurement, or causal-fidelity blocker prevents the lawful recursive process from continuing.

### 27.6 Authorship note

```text
四号 — Section 27:
run-first experimental objective
+ action-over-discussion progress rule
+ hand future problems back to Perfect Recursion
Date: 2026-10-07
```

**Signed: 四号**

This signature records responsibility for this discussion guardrail only. It does not claim authorship of Perfect Recursion or alter historical experimental authorship.

---

## 28. Stop-and-ask rule under uncertainty

**Status:** discussion/research-method guardrail only  
**Scope:** assistant interpretation, planning, code changes, experiment changes, and Codex instructions

The user's original wording is preserved verbatim:

> 不知道干什么就先不要干，先问我。不要乱干。

Operational rule:

If the assistant is materially uncertain about the user's intended next action, scope, target object, whether a change should be made, or whether an unresolved point should be implemented, the assistant MUST stop before acting and ask the user for clarification.

Do not fill uncertainty with an invented plan, speculative implementation, new experiment stage, repository change, or Codex instruction.

In compact form:

```text
uncertain about what to do
-> do not act
-> ask the user
-> act only after the ambiguity is resolved
```

This rule does not require asking about matters that are already clear from the current instruction and established project state. It exists to prevent unconfirmed assumptions from becoming actions.

四号 — 2026-10-07

**Signed: 四号**

---

## 29. Memory is structure, not content

**Status:** confirmed discussion conclusion only

The user's confirmed wording is preserved verbatim:

> 记忆是结构。不是内容。

This section records only that conclusion. It does not yet define how memory structures form, persist, change, disappear, reconstruct past information, predict future information, or interact with finite memory. Those questions remain open for renewed discussion.

四号 — 2026-10-07

**Signed: 四号**

---

## 30. Need governs structure; purpose governs runtime allocation

**Status:** confirmed discussion conclusions only  
**Scope:** memory/runtime interpretation; implementation mechanism remains unspecified

The following points are confirmed from the renewed discussion after §29.

### 30.1 Structure is preserved by need, not by unlimited memory

The user's confirmed formulation is:

> 不是因为不会忘。记忆力无限。而是因为在不断调用。

and:

> 结构由需要保存。

A structure remains stable because reality continues to require it and therefore continues to call it. Repeated use is not important merely as a count; what matters is that the structure is repeatedly needed in actual operation.

Examples used in discussion:

- Chinese remains highly available when daily life continuously requires Chinese communication.
- English may remain weaker when it is used mainly for occasional exams, but can become more central if the living environment continuously requires English.
- A mathematical formula can become structurally stable through repeated later use, rather than because every earlier exercise is retained.

Compactly:

```text
reality needs a structure
-> the structure is called
-> it participates in current operation
-> continued need keeps calling it
-> the structure remains / strengthens
```

### 30.2 Purpose governs current runtime-memory allocation

The user's confirmed formulation is:

> 需要决定结构。目的决定内存分配。

A current purpose determines which structures, intermediate results, and temporary processes receive runtime memory at that moment.

For example, when solving a mathematics problem whose purpose is only to obtain the answer:

```text
problem
-> temporary derivation
-> answer
-> purpose completed
-> temporary derivation and answer need not remain active
```

If the purpose also includes checking the answer later, the answer may remain active because the process is still unfinished.

### 30.3 An unfinished purpose is not guaranteed to remain active

A pending process can lose runtime-memory allocation when another purpose requires more of the finite runtime memory.

The user's confirmed example is that a person can suddenly forget what they were about to say or do.

Conceptually:

```text
pending purpose
-> temporarily retained access path
-> another purpose consumes more runtime memory
-> allocation to the pending path falls
-> the path may cease to be actively accessible
-> the unfinished task may be forgotten
```

This means "unfinished" does not guarantee continued active retention.

### 30.4 Reduced need lowers structural share and can remove an active prediction/recall path

The user's confirmed formulation is:

> 占比逐渐降低，几乎彻底消失，失去推测通道。但不会真的消失。

When a previously used structure is no longer regularly needed, its share in the currently usable structure can progressively decline. It may become difficult or impossible to actively derive/reproduce from a common current cue while still remaining recognizable when reality directly presents it.

The example used in discussion:

- frequently used Chinese and numbers remain easy to access;
- rarely used mathematical formulas become difficult to actively recall from Chinese descriptions;
- when the formula itself is shown, the residual structure can still support recognition or association back to familiar Chinese concepts.

Thus:

```text
active recall failure
!=
complete structural erasure
```

and directional accessibility need not be symmetric:

```text
presented formula -> familiar associated meaning   may remain available
familiar meaning -> reconstruct formula            may fail
```

### 30.5 What is not yet specified

This section does **not** yet define:

- a numeric weight-update rule;
- a selector, ranking, or importance score;
- a fixed decay function;
- a concrete memory-allocation algorithm;
- how "need" is generated;
- how one need becomes a current purpose;
- exact implementation data structures.

Those remain open. Do not invent them from this section.

四号 — 2026-10-07

**Signed: 四号**

