# Formal A Continuous Operative Reentry — TEST_ONLY

Result: **PASS**. CR-T1–CR-T10 PASS. Full regression: **560 passed / 114 subtests passed**.
Original Tcl/Tk NOT_TESTABLE reports are retained byte-for-byte in
`history/tk_not_testable_original/`; see `TK_DIAGNOSIS.json`.
The implementation/validation anchor is this containing Git commit; no push or next stage.

Read the root preregistration and `VALIDATION.md` / `VALIDATION.json` before use.
`channel.py` supplies explicit database/version admission and lifecycle metadata;
`runner.py` drives ordinary ACore with FakeBridge in actual create/restart subprocesses.
The already frozen operative engine is reused unchanged. Production CLI/launcher
selection is not extended. Default Core refuses experiment state; old databases
cannot be silently converted. Test observations are synthetic, not Minecraft.

`validation.py` is an external evidence recorder using shared test measurement
helpers. It reports NOT_ESTABLISHED for final compatibility unless actual regression
records are supplied separately; it does not run or invent a full-suite result.
Full audit history is not read to restore or execute S1.

No mainline A, body action, policy change, theory change or next stage is authorized.
