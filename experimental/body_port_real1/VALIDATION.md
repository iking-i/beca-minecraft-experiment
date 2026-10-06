# BPC-R1 validation — real-experience formation only

Result: **PASS** within the pre-registered independent TEST_ONLY offline scope.
No Minecraft was started and no formed connection was connected to execution.

## Actual real-history witness

- Individual: `A-71bc612c-8f2c-4f70-8d4d-3d38bed52942`.
- Session: `S-09272552-fb87-4078-871b-1c752b1d4862`.
- Experience: `03476345-ff88-4128-b64f-1adc22d8d1ad`.
- Action: `91b7ca9c-1881-4b01-b491-1a40aa5b4211`.
- Native port: catalog version `2`, numeric code `0`, empty parameters.
- Recorded frames: `E75 → E76`; protocol namespace `26.1`, body epoch `1`.
- Event cutoff: `3499`; 26 eligible experiences; the fixed identity-order
  algorithm chose this witness before formation, without examining formed results.
- Bootstrap selection remains `EXTERNAL_FIXED_POLICY`; binding source is
  `INITIAL_EXTERNAL_POLICY`, exactly as preserved in the real action record.

Read-only source database SHA-256 before and after:
`46a375aca6d9c81441c8968e7c377a546920caa8d4eef993b4276aa146d43053`.

## Input / formation / authorship

`RealExperience` keeps canonical immutable copies of the actual experience,
request, complete receipt, both frames, both raw WORLD_OBSERVATION events,
recorded native capability provisioning and session environment. Identities,
status, source event metadata and action authorship are not inferred or replaced.

`RealChange` contains all five recorded change facts with exact numeric identity.
This witness includes a changing numeric channel and four `unobserved` facts;
these are experienced observation differences, not asserted effects of code 0.
Coverage uncertainty remains visible. No action semantics identify which change
is caused by the input, and no causal law is claimed.

The codec emits two individually supported Member facts from one real execution
record: `Member(experience,C)` and `Member(experience,O)`. It emits no Shared edge.
Frozen BPC-0's unchanged generic `form()` then derives `Shared({C,O})` through
`SHARED_INCIDENCE`. A read-only verifier checks formed facts and all direct
supports and reports `CONNECTED`; it returns native identities, not expressions.

Thus code 0 originates in the historical external bootstrap, O originates in
the native catalog, C originates in real observation differences, and the new
connection instance originates in generic formation from actual record incidence.
Witness selection is an explicitly external measurement procedure, not output
authorship. This is offline processing of formal history, not integration into A.

## Negative controls

All twelve controls passed:

- Missing experience/port/change input is rejected before encoding.
- Removal of necessary experience, O identity or observation roots before
  formation prevents a **supported** connection.
- Detached post-formation screening of those roots or the formed edge prevents
  successful verification without recomputation.
- Disconnected TEST_ONLY distractors leave the original connection and direct
  supports unchanged.
- A detached two-native-port reader intervention returns `AMBIGUOUS` and both
  ports, with no adoption. Independent unit coverage forms two native-port
  connections from two explicitly synthetic schema records and also refuses
  adoption; this is not claimed as an additional real historical experience.

The formation routine can mechanically materialize unsupported topology if
orphaned Member facts are deliberately left by screening. Such topology is
never accepted as a supported connection; raw fact presence alone is not PASS.

## Evidence and tests

Unit tests: **29 passed**, using explicitly synthetic schema controls only.
The real acceptance witness is separately read from the existing canonical DB.
The exact real evidence, all formed facts/direct supports, rejection reasons
and source event digests are preserved in the local machine report:
`storage/validation/BPC-R1-REAL-HISTORY-003/validation.json`.
Compact portable evidence index: [VALIDATION.json](VALIDATION.json).
Earlier development measurements 001/002 remain separate and are not overwritten.

Runtime, catalog, caps, BPC-0, Successor-0, FROI, GSC, CEC, historical results and
theory were not edited. No sampler, binder, expression construction or real
perform call is part of this module. No second real execution, general parameter
formation, internally authored action, imitation, causal law or universal
generative dynamics is established. This stage stops at supported C ↔ O.

Regression: `pytest -q --ignore=tests/test_successor0.py` completed with **321 passed, 90 subtests passed** in 270.76 seconds. Successor-0 was not revalidated. JSON parsing, source hashes, whitespace checks and tracked-source diff checks passed. All existing tracked files remain unchanged; only the new isolated module/tests/reports are present. No commit or push was performed.
