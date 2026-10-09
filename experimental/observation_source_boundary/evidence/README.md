# Offline evidence only

COMPARISON.json is the paired E1–E32 saved-real-input/checkpoint comparison.
It records exact input hashes; original files and database were not rewritten.
The inputs were already collected by Continuous Capacity. They are not new live
observations, a replay-based live-chain PASS or evidence of new body execution.

RSS_OLD/NEW are separate-process measurements including diagnostic fixture
loading in process RSS; time is advance (and new-source commit), excluding
fixture loading. Measurements ran on a shared non-dedicated machine alongside
other checks. Treat timings as observed overhead, not a controlled speedup proof.
10ms RSS sampling may miss shorter peaks. Peak RSS did not decrease in this pair;
JSON shrinkage does not establish bounded memory or infinite operation.

FOCUSED/RELATED/FULL logs are actual ordinary Python tests, without Minecraft.
FULL_INITIAL collected 18 new tests; final focused includes all21. FULL_FINAL
records the final complete collection including the three later-added tests.
Overlapping test sets are not summed into independent acceptance evidence.

INITIAL_CONTROL_FAILURE preserves the initial incorrect capacity-test setup.
INITIAL_FAILURES.json records other actual debug/comparison failures without
inventing missing full trace logs. Frozen previous failures stay untouched.

PRESERVATION checks 512 earlier protected files, 27 unrelated files, 13 frozen
LF hashes and the original real database hash. Current indexes are unchanged
against the present HEAD as additionally verified by the empty tracked diff.
No SQLite, credentials or private configurations are exported.
