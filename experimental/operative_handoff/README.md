# Operative Handoff — isolated TEST_ONLY witness

Frozen boundary: `OPERATIVE_HANDOFF_TEST_ONLY_SPEC.md` at
`41aceb5f0b74f7be6eb186dd5e2c0a34ba1b5d8d`.

`Mechanism.advance(nodes, edges, active)` has one dependency traversal loop.
Both supplied and subsequently formed edges use the same `Edge` dataclass and
the same operative edge collection. Audit evidence is not an execution input.

The fixed formation law connects every previously participating terminal node
(no outgoing dependency in the prior graph) to every later observed node,
except self-pairs and existing edges. It does not select a preferred endpoint.
This is a TEST_ONLY temporal-frontier law, not a general theory claim.

`Runtime.advance()` executes the committed graph, forms new edges from the prior
processing and current observed input, then commits an immutable next state.
Formation does not execute edges. Subsequent ordinary advances use the newly
committed edge through the same mechanism, without a dedicated read/consumer.

The fixture declares nodes A/B/C and supplies only A→B. The first input activates
A. A later input observes C, forming B→C after execution. Later input A reaches
A/B/C. An edge-only ablation retains nodes, history and audit while masking B→C:
the same mechanism now processes only A/B. Reuse does not reconstruct B→C.

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_operative_handoff.py
.\.venv\Scripts\python.exe -m experimental.operative_handoff.validation
```

No formal runtime imports this package; it imports only its own modules and the
standard library. No Minecraft, body, sampler, binder, historical database or
old BPC/FROI/Successor consumer is involved. See `VALIDATION.md` and
`VALIDATION.json` for executed results and nonclaims.
