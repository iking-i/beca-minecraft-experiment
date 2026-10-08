# Initial probe record

Before focused tests, the first ordinary Core observation probe failed at
FrameEncoder.encode with KeyError: 'cursor'. The synthetic inventoryScreen
carrier record omitted the existing required cursor object. No formation or
acceptance result was produced. Fixed only the new synthetic carrier fixture
by supplying cursor: {}; existing encoder and all acceptance criteria unchanged.

First focused invocation without --basetemp: 19 setup errors in 4.54s.
pytest could not create numbered directories in the sandbox's default external
Temp directory. Tests did not execute. Subsequent invocations use fresh explicitly
named workspace .test-tmp directories; no fixture/test skips or criterion changes.
