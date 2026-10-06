# Formal conversation handoff — BPC-R1 phase closeout

Date: 2026-10-07 (Asia/Shanghai). Research-method boundary:
`00_DISCUSSION_CONSTRAINTS.md` §§16–24. Next phase is **NOT_STARTED**.

## Stable baseline and exact evidence anchors

- Repository: `iking-i/beca-minecraft-experiment`.
- Research publication branch: `codex/bpc-r1-real-formation`.
- Base / preserved BPC-0 closeout: `ebdcbc73d060ce894513f35853ed01c5d47836ef`.
- Implementation/specification/acceptance commit: `5fd85389e39801a0899eb0b1a4296796c2427783`.
- The separate phase-closeout commit contains this handoff. Resolve its exact SHA with
  `git log -1 --format=%H -- BPC_R1_CONVERSATION_HANDOFF.md`; do not invent a
  self-referencing SHA inside the commit.
- BPC-R1 specification: `experimental/body_port_real1/SPEC.md`.
- Original validation: `experimental/body_port_real1/VALIDATION.md` / `VALIDATION.json`.
- Full original local evidence: `storage/validation/BPC-R1-REAL-HISTORY-003/validation.json`.
- Separate closeout checks: `experimental/body_port_real1/CLOSEOUT_VALIDATION.json`;
  full local recheck: `storage/validation/BPC-R1-CLOSEOUT-001/validation.json`.
- Theory remains `iking-i/beca-architecture/main` at
  `546363ffd9e3f55cd22cd73ad2e91cc57f93bae3`. No theory changes.
- Successor-0 implementation `91eac86632af528251d73ecf4c80f283c87fe019` and status
  `13337f47a44ace65cb1704978dee01f82791c22d` remain frozen, without revalidation.
- BPC-0 implementation `996b6fab6d055159f1336085ec80e5a7a4f07613`, its synthetic
  PASS and original real-world NOT_TESTABLE result remain unchanged.
- FROI/GSC/CEC historical reports and classifications remain unchanged; regression
  tests are maintenance checks, not reopening or regenerating their acceptance.

Closeout tests: `pytest tests/test_body_port_real1.py -q` → **29 passed** in
0.18 seconds. Necessary regression: `pytest -q --ignore=tests/test_successor0.py`
→ **321 passed, 90 subtests passed** in 275.10 seconds. The excluded Successor-0
tests were not run. All 12 offline real-witness controls passed.

The compact closeout JSON records exact executed test counts, timing, audit
checks and source/report hashes. It is the current closeout measurement index;
prior validation files retain their original results and working-tree wording.
Existing unrelated untracked TEST_ONLY work remains excluded from the commit.
Remote main and the BPC-0 frozen publication branch are not modified.

## Completed object, scope and strongest accepted claim

**BPC-R1 = PASS / COMPLETED / FROZEN.**

Object: a supported history-formed `Shared({C,O})` instance, read and verified
inside an isolated offline TEST_ONLY realization. No body expression is generated.

```text
recorded real Minecraft experience
→ formal history / RealExperience
→ generic shared-incidence formation
→ supported C ↔ O
```

O already exists as native `(catalog version=2, numeric code=0)`. The experiment
does not create a new capability or translate an internal value into an action.
The trusted real source is individual
`A-71bc612c-8f2c-4f70-8d4d-3d38bed52942`, session
`S-09272552-fb87-4078-871b-1c752b1d4862`, experience
`03476345-ff88-4128-b64f-1adc22d8d1ad`, action
`91b7ca9c-1881-4b01-b491-1a40aa5b4211`, frames `E75 → E76`.

The pre-registered identity-order measurement selected one of 26 eligible real
experiences without inspecting formed results. Full receipt, two actual encoded
frames, raw observations, experience, request, capability provisioning and session
provenance are retained as nine roots, with 15 direct supports. Numeric values
and coverage/unobserved changes are preserved exactly; no synthetic-integer
fixture substitution, epsilon, similarity or semantic matching was introduced.

The codec creates supported `Member(experience,C)` and `Member(experience,O)`.
Unchanged BPC-0 generic `form()` creates the Shared edge; it is absent in seeds.
Read-only verification consumes formed facts/supports and returns all native ports.
Missing necessary input/support prevents a supported connection, distractors
preserve the connection, and multiple ports yield ambiguity with no adoption.
Unsupported orphan topology may remain after detached screening; raw edge presence
alone is not accepted as a supported connection. All 12 controls passed.

## Authorship and nonclaims

Historical bootstrap code remains `EXTERNAL_FIXED_POLICY`, and historical binding
remains `INITIAL_EXTERNAL_POLICY`. Witness selection is an external measurement
procedure. Reification, generic formation and support verification are disclosed
fixed mechanisms; only the concrete connection instance is experience-conditioned.
Source authenticity assumes trusted pre-existing local records, not adversarial
sensor authentication. Observation change is temporal association only.

This phase does **not** prove:

- the historical action was produced by internal structure;
- O caused the observed world change;
- behavioral authorship;
- general parameter formation;
- autonomous goals;
- behavioral causal closure;
- that C ↔ O already controls a real body.

It also does not prove imitation, a causal law, generalization, universal generative
dynamics or upward recursion. No runtime, body, catalog, caps, frozen BPC-0 evidence,
canonical database or theory was modified. No Minecraft/A was started. There is
no `C ↔ O → real perform()` adapter and no sampler/binder fallback in this module.

## Next boundary — NOT_STARTED, no design or execution authorized here

```text
real-history-formed C ↔ O
→ subsequent real body execution
```

Question recorded for a separately authorized future phase:

> 一个由真实 Minecraft 历史形成并验证的 C ↔ O，能否在不经过外部 sampler、binder 或人工 value-to-action mapping 的情况下，直接成为后续真实 primitive body expression 的动作来源？

This handoff records a research boundary only. It contains no next-phase mechanism,
architecture, interface implementation, output policy or experiment design.
Do not start that phase, modify runtime, create an execution adapter, invoke real
perform or start Minecraft under this closeout authorization. Stop after publication.
