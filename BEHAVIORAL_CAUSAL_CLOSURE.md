# Behavioral causal closure — v0.9 reference

## Pre-implementation audit (2026-10-04)

This section was written before implementation. Experiment HEAD: `1c165168cd5845e43d4dd334e6491cbc36118c9e`; theory HEAD: `89a56ad7ce236adfcb52b13d3e6fe7014ff88ddd`. The three current theory sources were read at that exact commit: SPEC.md, EXPERIMENTAL_IMPLEMENTATION_BOUNDARY.md and INDIVIDUAL_CONTINUITY.md. WORLD_ENTRY_FREEZE.json remains an unchanged historical acceptance of the body, not acceptance of behavioral authorship.

### Actual formal causal graph before changes

| Edge | Executed implementation | Classification | Evidence / boundary |
|---|---|---|---|
| World → ObservationFrame | observation.FrameEncoder.encode:40; core.ACore.accept_observation:115 | EXTERNAL_FIXED_MECHANISM | Existing numeric channels/opaque references; sensor coverage is ENVIRONMENT_CONSTRAINT. |
| Frame → differences | change_detection.detect_changes:22; formal_l0.FormalL0Engine.advance:117 | EXTERNAL_FIXED_MECHANISM | Compare numeric values, not meanings or reward. |
| Differences → units | structure.pattern_id:16; formal_l0.advance:119 | EXTERNAL_FIXED_MECHANISM | Hash labels only identify change patterns; this hash does NOT select actions. Observed pattern contents are INTERNAL_VARIABLE_STRUCTURE. |
| Previous unit + pending actions + next frame → experience | formal_l0.advance:172–191 | EXTERNAL_FIXED_MECHANISM | Temporal association only; actual parameters are in experience.action_parameters. No observation-to-action prescription. |
| Experience → partial → relation evidence | formal_l0.advance:196–268 | EXTERNAL_FIXED_MECHANISM | Persistent process publishes; bounded evidence insertion. Created relation/outcome contents are INTERNAL_VARIABLE_STRUCTURE. |
| Relation / integration → stored feedback | formal_l0.advance:270–278 | INTERNAL_VARIABLE_STRUCTURE | next_relation_ref and expected_outcomes refer to actually accumulated evidence. Assignment/read algorithm is EXTERNAL_FIXED_MECHANISM. |
| Feedback → next recursive read | formal_l0.advance:196–217 | INTERNAL_VARIABLE_STRUCTURE | relations[feedback.next_relation_ref] determines read_succeeded/expected_outcomes. Real recursion-side causal edge. |
| Internal relations → action candidates | core.execute_discrete_action:217–224 | EXTERNAL_FIXED_POLICY | **Missing edge**: candidates are body.action_space currently_available, not produced by relations. Availability itself is ENVIRONMENT_CONSTRAINT. |
| Available codes → chosen code | formal_l0.select_uniform_action:296–315 | EXTERNAL_FIXED_POLICY | formal.action_sampling LCG, random_state → codes[after % len(codes)]. pattern_id is output metadata only. |
| Frame/legal domains → chosen parameters | action_space.bind_parameters:75–152 | EXTERNAL_FIXED_POLICY | action.parameter_binding + LCG domain selection; some fixed defaults. Domain legality is ENVIRONMENT_CONSTRAINT; selecting a domain element is policy. |
| Code + parameters → perform RPC | action_space.formal_command:155; core.execute_discrete_action:231–277 | EXTERNAL_FIXED_MECHANISM | Dispatch/record/transport an already selected command. |
| Body input → world consequence | frozen Minecraft body/native inputs | ENVIRONMENT_CONSTRAINT | Native Minecraft state/physics/protocol, independently validated in world-entry acceptance. |
| Consequence → fresh frame → experience | core.tick:333–361; accept_observation:115 | EXTERNAL_FIXED_MECHANISM | Fresh observation can update relations; this does not close the missing behavior edge. |

### Breakpoints and representation insufficiency

1. `units`, `relations`, `latest_integration`, `latest_generation` and `feedback` are not read by the formal code selector to determine its result. Provenance references alone are not causal dependencies.
2. `random_state` is stored in InternalState but originates in external initialization and is advanced by an external recurrence. It is not a history-formed behavior structure.
3. Relations retain antecedent, action_code, outcomes, counts and bounded evidence references. **They do not contain an executable behavioral expression, a history-formed selection/control relation, or parameter bindings.** Parameter values remain in experience/partial audit records. The full append-only journal is not an unlimited A-facing memory port.
4. `decision_authorship` checks source labels; it does not resolve historical references or prove a readout depended on them. Existing formal labels are correctly external; a future internal label alone would be insufficient.
5. `PolicyRegistry.validate_internal_proposal` does not generate, verify or activate proposals. It explicitly returns activated=false. No hidden internal policy generator exists.

Writing “match a prior antecedent then replay its action”, “choose most recent/frequent relation”, “continue successful action”, or hashing relations into a seed would fill this gap with EXTERNAL_FIXED_POLICY. Storing that rule in InternalState would not change its authorship.

## Implementation boundary selected after audit

Implement only the strictly demonstrable portion allowed by the task's insufficiency clause: an offline, evidence-resolving authorship audit, paired legitimate recursive histories, and isolated relation ablation. Do not invent an internally authored behavior output. Do not change the formal sampler, parameter binder, core execution, frozen body, resource ceilings, identity/death handling or historical data. This is diagnostic preparation, **not an implemented behavioral-expression producer/readout**.

Minimal missing structures for a later implementation are: a bounded, recursively writable behavior-expression representation (numeric code and every required parameter/reference, lineage included); a recursively produced control/binding relation that determines which expression reaches a port; and a generic type/domain-checked executor. The executor must not supply selection, replay, arbitration, target rebinding, adaptation direction or repair. Merely declaring those fields cannot supply their formation process. This audit does not prove such a formation mechanism impossible; it proves it is absent in the current implementation.

## Post-implementation evidence

**BEHAVIORAL_CAUSAL_CLOSURE = failed for the current formal path; implementation_scope = diagnostic_partial.** The implemented audit/validation passes its regression tests. This does not mean the requested behavioral closure passes. The representation/producer/readout is missing; no covert replay or adaptation policy was added to supply an answer.

### Graph after changes

The entire runtime graph above is unchanged. A parallel, offline EXTERNAL_FIXED_MECHANISM now resolves:

```text
stored ACTION_REQUESTED + prior experience / partial / integration
    → behavioral_audit.action_trace
    → code and per-parameter author report (not fed back into A)

two independent TEST_ONLY histories through actual formal Core/engine
    → substantive relation comparison
    → same-frame / same-bootstrap formal readout comparison
    → relation ablation in detached copies
    → negative control report
```

`individual/behavioral_audit.py` is never imported by Core, the interpreter, the binder or the body. Full journal access is for the offline auditor only. It requires an explicit existing checkpointed DB and refuses nonempty WAL to avoid both stale reads and canonical SHM writes. The fixture creates separate per-individual folders and does not replace the canonical selection or acquire its lease. Canonical integrity checking observes file metadata and hashes small files; it does not hash the entire large DB or infer subject continuity from persistence.

### Actual paired histories

Validation lifetimes:

- `A-6a7d5918-6711-4b3c-a3d8-f63866cd7262`
- `A-434ac31a-24c2-4703-a1ad-126401e685dd`

Each is registered separately, then runs the existing formal engine, SQLite state chain and frozen Body `perform` RPC with the existing CapabilityBot test carrier. These are **not real Minecraft observations**. The controlled numeric histories offset the same base x-coordinate by `[0,1,0,1,0]` versus `[0,2,4,6,0]`, then both receive the same current raw observation. No behavioral choice variable is assigned. Both initial bootstrap states are explicitly initialized to 0, not derived from history. Logical caps are frozen defaults; both unmonitored fixtures explicitly have empty resource caps, not validated OS quotas.

Persisted frames retain each individual's ID; all current perceptual/body/domain content is identical. For exact full-frame counterfactual equality, both detached readouts use the **same** `TEST_ONLY:common-frame`, without rewriting either DB. The paired histories genuinely produce different evidence after removing IDs/UUIDs from comparison: relation `U-ee9cd61aee438f8f69d4:-1` has evidence_count 2 with one outcome in the first history, versus count 3 with two outcomes in the second. Counts are observations, not a voting/selection rule.

Both formal selectors still produce `perform(code=46, parameters={})` from the same available codes and external seed recurrence `0 → 1013904223`. The actual unmodified Core requests agree as well. Code 46 is the frozen hand-swap input: the fixture records ACTION_REQUESTED at A9 / event 85, ACTION_EXECUTED at A10 / event 88, then WORLD_OBSERVATION at A11 / event 90. This is fixture execution and renewed fixture perception, not a real Minecraft consequence or an internally authored behavior chain. Detached parameter probes examine **all 32 currently available codes**, rather than choosing examples until different behavior appears; every paired parameter result is identical. For example, code 16 binds slot 7 in both; code 15 binds inventory_slot 36, the same opaque reference_block, face 1 in both, entirely through the external binder. These probes are not dispatched and do not count as live actions.

### Concrete provenance, and why it is not causal authorship

First validation A, ACTION_REQUESTED source A8 / structure_revision 6:

```text
E5 → E6
experience 335195be-040a-4d38-9684-923550cc8e81
    → partial 0eb50cf0-6bcb-4bac-b23f-717dc6004b3a
      process 52406637-0e2c-4bb1-810e-2e0240e05cc8
    → integration 1ddd80a4-10c0-40b8-a93d-06ea128861d4
    → relation U-0294313806f11063b38a:-1
```

These references resolve to actual prior events; the partial's experience matches the original experience. However, code selection does not consume that relation. `formal.action_sampling` determines 46; `action.parameter_binding` remains the declared parameter author. The audit therefore reports `references_resolved=true`, `behavioral_dependency_proven=false`, `ongoing_external_author=true`, `audited_authorship=EXTERNAL_FIXED_POLICY`. An integration ID attached to a request is not a witness of dependence.

### Ablation

On a detached copy of the first current state only, remove `relations`; retain the exact current frame, original feedback pointer, sampler/binder, bootstrap, capabilities and ceilings. The next actual interpreter read changes:

| Witness | Original | Ablated |
|---|---|---|
| requested_relation_ref | U-0294313806f11063b38a:-1 | same |
| read_succeeded | true | false |
| expected_outcomes | U-ee9cd61aee438f8f69d4, U-4f53cda18c2baa0c0354 | empty |
| Formal action / parameters | 46 / {} | 46 / {} |

The audit compares actual read success/outcomes, not random limit UUIDs. This is evidence for **history → internal structure → later recursive processing**, and negative evidence for the proposed behavior dependency. It is not a passing behavioral ablation.

### Bootstrap and authorship boundary

No ongoing behavior is reclassified as internal. Without a prior EXPERIENCE_FORMED, the formal externally sampled input may be reported `PURE_EXTERNAL_BOOTSTRAP`. Once history exists, ongoing wholly external selection remains **EXTERNAL_FIXED_POLICY**, explicitly outside the passing closure categories; calling it MIXED_POLICY would falsely imply an internal behavioral contribution. Internal-labelled selection plus an external binder remains MIXED_POLICY but not proven internal. Explicit tests stay TEST_ONLY. Internal labels alone are UNVERIFIED_AUTHORSHIP until actual producer/readout and counterfactual evidence exist.

The current path violates the desired bootstrap-only boundary by continuing external sampling; this violation is reported, not secretly fixed by disabling capabilities or installing a replacement host policy. No internal behavioral expression has yet formed.

### Evidence, tests and scope limits

- Small checked-in evidence: [BEHAVIORAL_CAUSAL_CLOSURE.json](BEHAVIORAL_CAUSAL_CLOSURE.json), including both IDs, source refs, substantive relation differences, commands, all parameter probe results and ablation.
- Full local report for each A: `storage/individuals/<id>/reports/behavioral-negative-control.json`; SHA-256 `9d99affb7586135459578ec0e224cd186103892a6934eed28439d7cfc7f76ce6`. Full DBs/reports remain untracked.
- Python full suite **141 passed**, including eight new tests; after final ablation witness tightening, the eight affected tests passed again. Node **42 passed**; existing JavaScript syntax checks passed. Initial Node sandbox transport tests returned EACCES; the unchanged suite passed with localhost TCP permitted, without weakening assertions.
- All WORLD_ENTRY_FREEZE component hashes and the manifest itself remain unchanged, as checked by the existing full-suite freeze test. All production behavioral code, configs and physical caps remain unchanged. No canonical runtime, Session, lease, DB or sidecar write path was used. Guard before/after matched.
- `BEHAVIORALLY_BINDING_LIMIT = not_tested_in_this_fixture`: detached memory failures are not a new real-world claim; earlier V0-A/V0-B evidence remains separate.
- No new real Minecraft closure run was performed: its internal-author prerequisite already fails. Prior TEST_ONLY world-entry server evidence cannot be borrowed to turn this result into passed. Fresh fixture frames do not prove Minecraft consequences.
- No L1, intelligence, learning-success, survival/death mechanism, new body capability, environment expansion or autonomous policy migration is claimed.

### Reproduce

```powershell
.\.venv\Scripts\python.exe -m debug.behavioral_validation
.\.venv\Scripts\python.exe -m individual.behavioral_audit --db storage/individuals/<validation-id>/individual.db
.\.venv\Scripts\python.exe -m unittest discover -q
npm --prefix minecraft test
```

The first command explicitly creates two new diagnostic fixtures, preserves old validation reports and does not select either as the original A. It is not the formal startup entry point. Ordinary formal startup remains `main.py` and remains externally driven.
