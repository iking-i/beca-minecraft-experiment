# Operative Connection Interpretation Erratum

**Date:** 2026-10-07

**Status:** AUTHORITATIVE_CURRENT_INTERPRETATION_CORRECTION

**Scope:** experiment repository interpretation; not a Perfect Recursion theory
amendment, runtime implementation, new experiment, or retroactive rewrite of
historical evidence. Frozen baseline: `codex/bpc-live-1` at
`916ccf4f83243346341ea3e3cbf5e41e06991cff`. BPC-LIVE-1 remains
**PASS / COMPLETED / FROZEN**. Next experimental phase remains **NOT_STARTED**.

## 1. Preserved experimental facts

BPC-0, BPC-R1, BPC-R2 and BPC-LIVE-1 retain their actual evidence and frozen
results. Their respective scopes establish:

```text
C, O
→ Member / Shared represented relation formation
→ supports / provenance
→ persistence where applicable
→ specialized consumer recovers / consumes the represented relation
```

BPC-LIVE-1 additionally establishes:

```text
real current input → current C
→ live represented C/O relation formation
→ persistence inside the same A state chain
→ later real recursive cycle
→ specialized live consumer reads the saved represented relation
→ read affects recorded recursive processing/output
```

Canonical A7/E3 saved 47 supported relations; A8/E4 read those saved relations.
The later new-formation RESOURCE_LIMIT and both earlier NOT_TESTABLE attempts
remain unchanged. This correction neither retracts the scoped facts nor expands
their acceptance criteria.

## 2. Correction of the stronger interpretation

The previous interpretation of `Shared(C,O)` or `Shared(C,O) → consumer → O`
as an established operative body-port connection was too strong. The actual
implemented chain is:

```text
C + O → Member(C), Member(O)
→ third-party Shared relation object
→ persistence
→ specialized consumer / consume_saved
→ returned O/reference
```

Shared does not modify C or O's ordinary recursive running topology. Without
the specialized consumer, normal FormalL0 does not naturally traverse O because
Shared exists. Under current evidence:

```text
Shared(C,O) != OPERATIVE_CONNECTION(C,O)
classification = REPRESENTED_RELATION
```

“Represented structural incidence” or “supported represented relation” is
accurate. An unqualified claim of validated operative structural connection is
not justified.

Direct code anchors at the frozen baseline:

| Source / function | Actual role and limit |
|---|---|
| `experimental/body_port0/prototype.py`: `Member`, `Shared`, `form`, `consume` | Forms a separate Shared fact from common Member incidence; a specialized consumer recovers a supported endpoint. |
| `experimental/body_port_real1/prototype.py`: `connections` | Inspects formed facts/supports to recover body-port endpoints. |
| `individual/live_body_structure.py`: `advance_structure` | Writes Frame, BodyPort, CurrentChange, Member and Shared facts/supports into the saved live graph. |
| `individual/live_body_structure.py`: `consume_saved` | Uses saved feedback and supported Shared facts to return connection IDs, ports and root witnesses; does not install an ordinary FormalL0 dependency. |
| `individual/formal_live_body.py`: `FormalLiveBodyEngine.advance` | Reads the prior graph, calls `super().advance(...)` without that read as an operand, then attaches `live_body_connection_read` to partial processing and process output. This is a real recorded output effect, not evidence that base FormalL0 now traverses C→O. |

## 3. Historical “connection” names

Body-Port Connection stage names, filenames, class names, historical commits
and reports remain unchanged. Naming is not evidence of operative topology.
After this correction, “BPC connection” without further qualification denotes
the historical experimental object, interpreted within this erratum's scope.
Any OPERATIVE_CONNECTION claim requires the working criterion below.

## 4. Correct interpretation of BPC-R2

BPC-R2 PASS is preserved. Within its fixed TEST_ONLY unique witness:

```text
represented relation
→ specialized unique consumer
→ unique supported native O
→ mechanical projection of O.code into a parameterless expression
→ real perform and matching execution receipt
```

`experimental/body_port_real2/prototype.py::expression_from_formed` uses the
specialized supported-connection read and native-code projection. This proves
the stated fixed-witness chain. It does not establish a live A operative C→O
connection or internal behavioral authorship. It cannot be concatenated with
BPC-LIVE-1 PASS into an operative live loop that was never executed.

## 5. Correct Formal L0 baseline

Formal L0 is not a causally inert recorder. Existing scoped evidence includes:

- History changes later relation/outcome reads.
- Feedback references change later operands.
- Relation contents change expected outcomes and comparison.
- Consequences can re-enter later recursion.
- FROI has genuine scoped internal causal effects.

`individual/formal_l0.py::FormalL0Engine.advance` reads the feedback relation
reference and its outcomes, records distinct experiences, and updates feedback.
`integration/froi.py::consume` reads formed organization facts; in
`individual/formal_froi.py::resume_from_read_checkpoint`, read outcomes enter
expected outcomes and failures produce consequences for later processing.
These actual dependencies must not be erased by this correction.

What has not been established is generic operative structural mutation:

```text
history/current recursion forms a new operative edge X→Y
→ that edge becomes part of the running recursive organization
→ normal later recursion through X actually depends on / traverses Y
→ no relationship-specific semantic consumer assigns the edge its effect

GENERIC_OPERATIVE_STRUCTURAL_MUTATION_ESTABLISHED = NO
OPERATIVE_CONNECTION_ESTABLISHED = NO
```

These are evidence-status statements, not claims that such capabilities are
impossible or that all existing structural formation is causally ineffective.

## 6. Minimum falsifiable working criterion

This is a working experimental criterion, **not** a Perfect Recursion axiom,
new stage definition, or replacement of frozen historical acceptance criteria.
An operative connection claim requires at least:

1. **FORMATION:** Y was absent from X's prior running dependencies; history or
   current recursion produces an identifiable new edge instance.
2. **OPERATIVE ADOPTION:** the edge enters the running recursive organization
   as an actual operand, dependency or routing element. A relation index,
   provenance record, log or output attachment alone is insufficient.
3. **NORMAL REENTRY:** the same normal recursive advance later processes X
   through or in dependence on Y because of that formed edge. No extra manually
   designated query root or relation-specific semantic consumer supplies its
   running meaning.
4. **EDGE ABLATION:** hold X, Y, input and other state fixed; mask only the formed
   edge. The actual later processing path or Y participation must disappear or
   change. Fewer query results alone do not establish this.
5. **STRUCTURAL REUSE:** the edge itself belongs to the running structure and
   remains referenceable, usable or recursively acted upon under the same
   generic semantics. Re-deriving a descriptive record each time is insufficient.

Generic interpreters, pointer dereference, graph engines and mechanical
executors are allowed. The distinction is between generic execution of a formed
edge and a specialized relation-record query followed by an externally assigned
effect. An interpreter's existence alone is not contamination.

## 7. Error classification

```text
PRIMARY:
  EVIDENCE_OVERCLAIM
  EXPERIMENTAL_MODEL_MISMATCH

NOT ESTABLISHED AS:
  implementation bug
  theory falsification
  theory amendment requirement
```

The experiments formed represented relations with real causal effects under
specialized consumers. The error was promoting that evidence into the stronger
claim of operative topology/connection. This does not amend Perfect Recursion.

## 8. Historical protection and stopping boundary

All frozen BPC-0, BPC-R1, BPC-R2 and BPC-LIVE-1 code, evidence and PASS results
remain intact. NOT_TESTABLE attempts, raw validation evidence, original handoffs,
commit hashes, test counts, Minecraft evidence and Successor/GSC/FROI/CEC history
are preserved. No historical file is rewritten to imply this interpretation was
already known. This erratum is a later interpretation correction.

This correction defines no solution, operation vocabulary, runtime change,
action/parameter mechanism or new experiment. Next experimental phase:
**NOT_STARTED**.
