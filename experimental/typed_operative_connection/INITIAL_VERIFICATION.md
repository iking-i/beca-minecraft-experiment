# First verification record — retained

The preregistered law and criteria were not changed.
First smoke probe (fresh TEST_ONLY DB, Core observations 0 -> 1): S1 formed from
one exact same-channel fact; next ordinary pre-commit processing used it.

First focused command:
`.venv/Scripts/python.exe -m pytest tests/test_typed_operative_connection.py -q --tb=short --basetemp=.test-tmp/typed-focused-first`

Result: **1 failed, 19 passed in 10.78s**.
Failed ID: `test_two_changed_channels_all_actual_transitions_no_product_pairing`.
Expected only 0 -> 1 and 0 -> 20. Actual also included 0 -> -20. The synthetic
fixture changed self z while entity world z stayed fixed, so the existing
FrameEncoder mechanically changed entity-relative z. That third observed
ChangeSet fact is lawful and must not be deleted. The test expectation was
corrected to include it; the formation rule and frozen acceptance were not changed.
This was a test expectation error, not a forbidden output selector or altered codec.

After this run, complete advance now explicitly revalidates connection capacity
before/after the inherited transition as well as at read/formation/Core commit.
This closes admission at the engine return boundary without changing capacity.
A second value pair 20/64 was added to test the same law on different contents.
Later successful results do not overwrite this failure record.

Second focused invocation: 21 passed in 10.55 s after correction/addition of
the 20/64 history pair. Third focused invocation: 24 passed in 11.40 s after
adding absent-successor, invalid restart/mode and canonical-erasure controls.
The final validation invocation reruns all 24 focused tests against the final
code and external commit-journal recorder; it is recorded separately.
