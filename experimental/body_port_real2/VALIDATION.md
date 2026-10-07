# BPC-R2 validation

**BPC-R2 = PASS** under the previously frozen TEST_ONLY fixed-witness boundary.
Implementation is currently local working-tree material, not a frozen commit.

## Material and causal chain

Unchanged BPC-R1 experience `03476345-ff88-4128-b64f-1adc22d8d1ad`, frames E75/E76,
native catalog version 2 / code 0, parameters `{}`. Saved S and C were decoded from
the original report with SHA-256
`304166194dfd927667a74eaca5d0b42dd5935ae015ebe8bcafa91182e4655814`.
No history rescan, witness switch or formation rerun occurred.

```text
saved supported C ↔ O + fixed externally provided query C
→ formed-only support consumer → unique native O
→ expression.code = O.code, parameters = {}
→ unchanged Bridge/body mechanical dispatch
→ one real perform request → matching real execution receipt
```

The native catalog was compatible; code 0 was formal-enabled and available, with
both empty required parameters and empty parameter properties. On the user-supplied
port 61875, the independent TEST_ONLY body `BPC_R2_Test` sent exactly one request.
It was not the formal A and did not displace the formal A's username or write its DB.
The body session closed afterward. Reconnection was disabled; no action retry.

Receipt preserves code 0, parameters `{}`, started/finished timestamps and
`{input_sent:1,effect_acknowledged:0}` with `temporal_observation_only` attribution.
Observed receipt position was unchanged; no world-effect success condition was
introduced, and no world change is claimed. The frozen criterion concerns code
authorship and completion of the real input-execution path, not a movement/effect law.

## Authorship and controls

The expression consumer has no raw historical request/receipt argument. Its code
comes from the unique BodyPort endpoint reached through supported Shared facts.
The expected fixed code is used only to validate authorized witness/execution
scope, never as the consumer's generated value. A detached code-origin probe
substituting another supported port changes the consumer output while the old
historical action record remains unchanged; this probe is never executed live.

All eight detached checks passed: connection removal; necessary O identity/support
removal; inaccessible organization; ambiguity without adoption; unrelated
distractor invariance; invalid connection without sampler fallback; valid expression
with binder forbidden; zero sampler/binder/formation/Bridge calls in controls.
One-shot ledger and timeout/error unit controls also prove no automatic second send.

Query root, execution trigger, test body creation and timing remain external.
Generic consumer/unique-result adoption and native dispatch remain fixed mechanisms.
This establishes only the scoped formed-connection origin of this action code,
not endogenous goals/timing, general parameter formation, general behavioral
authorship/closure, O-caused world effects, imitation, universal dynamics or L1.

## Evidence and tests

Dedicated tests: **15 passed** (0.32 s) using an isolated workspace temporary
directory. An initial attempt could not create pytest's sandbox default temp
directory (6 tests passed, 9 setup errors); rerunning with a new workspace temp
directory resolved the environment issue without changing tests or predicates.

Related Python regression: **336 passed, 90 subtests passed** (284.55 s), using
a new isolated workspace temporary directory. The frozen Successor-0 tests were
explicitly excluded (`--ignore=tests/test_successor0.py`) to avoid reopening that
stage; its files/results were not modified.

The real acceptance report is `storage/validation/BPC-R2-LIVE-001/validation.json`;
the pre-live offline report remains separately at `storage/validation/BPC-R2-OFFLINE-001/validation.json`
with overall NOT_TESTABLE because no real execution had yet happened.
The permanent one-shot reservation is `storage/validation/BPC-R2-ONE-PERFORM.json`.
Those files are retained locally; the compact machine index is [VALIDATION.json](VALIDATION.json).

No runtime/body/catalog/caps/BPC-R1/other frozen stage/theory file was modified.
No commit or push was requested/performed in this implementation round.
