# Continuous Capacity public evidence

These are exports of already completed runs, not new observations or experiments.
`run1` preserves the first recorder stop with raw classification FAILURE.
`run2` preserves the separate fresh 32-frame BUDGET_COMPLETED run, including death
and TEMPORAL_LINK_UNRESOLVED. They are not one continuous individual.

Large/raw files are exact-byte gzip+base64 JSON envelopes (`*.raw.json`). Decode
`data` with base64, then gzip decompress, and verify `original_bytes` and
`original_sha256`. This preserves whitespace and reduces repeated full-state
material without deleting evidence. Export is outside A and never a formation
source. SUMMARY/origin and test stdout are readable copies; EXPORT_MANIFEST.json
records their original byte hashes and local provenance. Git's existing newline
conversion is recorded separately in the closeout, not silently treated as an
exact source-byte hash match.

Both attempts include raw ObservationFrames, before/after committed states,
events, perform transport, original REPORT, origin and bridge stderr. SQLite,
sidecars/locks and private body configuration stay local; only DB hashes and
read-only authority checks are public. There is no complete-suite test result for
this stage. The two raw test logs document 17 pre-correction related tests and
6 corrected-recorder tests; they must not be summed as independent cases.

Original local data and collection-time reports are unchanged. The initial pytest
temporary-directory failure is recorded in PREFLIGHT.json; no unavailable raw
trace is fabricated. RECORDER_CORRECTION.md records the guard/instrumentation
correction before run2. Death cause remains NOT_ESTABLISHED.
