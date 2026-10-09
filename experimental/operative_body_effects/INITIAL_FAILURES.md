# First focused run — preserved

Command: pytest tests/test_operative_body_effects.py -q, workspace fresh basetemp
`.test-tmp/operative-effects-first-20261009`.

Result: 13 passed, 1 failed (15.35 s).
Failure: `test_no_filler_or_physical_order[receivers1-CONCURRENT_PHYSICAL_OPERATIONS]`.
Expected CONCURRENT_PHYSICAL_OPERATIONS, actual UNAVAILABLE.

The second test receipt used catalog code31, whose formal_enabled declaration is
false. The implementation correctly refused this port before physical dispatch.
The concurrency test now uses two actual formal-enabled native declarations.
This is a correction of the test carrier; no native declaration, acceptance
criterion, capacity or production condition is changed. The original first-run
fresh databases remain in the above temporary directory.
