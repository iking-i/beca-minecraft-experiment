# BPC-R2 — formed body-port action-code authorship and execution

Independent TEST_ONLY implementation of [the frozen boundary](SPEC.md).
Loads the single BPC-R1 saved organization by exact report SHA-256; no history
selection, producer execution or new formation. The consumer reads only formed
facts/supports and copies the returned native port's code into a zero-parameter
expression. Body dispatch is mechanical; it is not an action selector.

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_body_port_real2.py -q --basetemp <new-empty-test-directory>
.\.venv\Scripts\python.exe -m experimental.body_port_real2.validation --output <new-offline-report-directory>
```

The real one-shot witness has already been executed. Do not repeat it.
`storage/validation/BPC-R2-ONE-PERFORM.json` retains the exclusive reservation;
changing an output directory cannot clear it. Do not delete/reset that ledger.
The live entry checks all detached controls before starting the existing Bridge,
uses an independent TEST_ONLY body, disables reconnection and never retries perform.
No canonical A database, runtime, catalog, caps or prior frozen evidence changes.

Original real report: `storage/validation/BPC-R2-LIVE-001/validation.json`.
The unit fake-Bridge success cases are explicitly not real-world acceptance.
See [VALIDATION.md](VALIDATION.md) and [VALIDATION.json](VALIDATION.json).
