# BPC-0 — History-Formed Body-Port Connection (TEST_ONLY)

Read `SPEC.md` for the question and frozen acceptance scope. `prototype.py` is
independent of Core, FROI, GSC, CEC and Successor-0. The only production import is
the existing action catalog and mechanical `formal_command` packager.

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_body_port0.py -q
.\.venv\Scripts\python.exe -m experimental.body_port0.validation
```

The second command prints evidence; it does not write a database or launch a body.
No expression is emitted for missing, inaccessible, incomplete or ambiguous
connections. Exposed ports have native catalog identities and no parameter schema;
no handwritten value-to-code conversion or parameter defaulting occurs.

Fixture receipts and renewed observations are synthetic. The recording executor
records the expression and accepts independent fixture input; it does not implement
Minecraft physics or capability semantics. Real body/world validation is not done.
