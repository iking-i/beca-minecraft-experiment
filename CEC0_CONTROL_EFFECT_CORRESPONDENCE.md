# CEC-0 Control–Effect Correspondence — TEST_ONLY

Baseline: `3568901b5c41394e355a63c2654b994452967d1f`. Branch: `cec-0-control-effect`. Measurement HEAD: `3568901b5c41394e355a63c2654b994452967d1f`.
Implementation was uncommitted additions when measured; this document does not invent a future commit SHA.

## Frozen test boundary

T1 exact control identity across contexts; T2 exact consequence identity across records;
T3 all forward results; T4 all reverse results; T5 detached Shared-only access screening;
T6 no selection, semantics, ranking, execution, or parameter completion.
No GSC production rule or formal runtime changed. The codec uses the frozen Engine directly.

## Actual results

Independent tests: 17/17 passed. Fixture T1–T6: PASS.
Forward fixture read returns both Y1 and Y7; reverse returns both C3 and C9.
Screening all corresponding query/record Shared witnesses produces empty results;
screening one endpoint's witnesses reduces the set by one. Input/Condition/records/proofs
remain unchanged and closure is not re-executed during screening.
Negative pair has different control and consequence and no matching Shared incidence.
Adding a disconnected record and renaming record identities preserve query results.
Source-ID, source-order and seed-order controls preserve results; distinct catalog versions
produce distinct control identities. Parameter mismatch is rejected, not silently pooled.

Fixture is fully synthetic legal-source material from experimental/cec0/fixtures.py.
It is not existing-A empirical validation. Exact events, supports, roots, and returned endpoint
→ record → Shared evidence are saved in the adjacent JSON. Consumer takes no raw history;
removing raw producer material from its view does not change answers.

## Existing formal source

Database: `storage/individuals/A-71bc612c-8f2c-4f70-8d4d-3d38bed52942/individual.db`. Individual: `A-71bc612c-8f2c-4f70-8d4d-3d38bed52942`.
Session: `S-09272552-fb87-4078-871b-1c752b1d4862`. State range: [1, 588].
End reason: `core_ram_limit`. Entire fixed ended session examined, no favorable checkpoint search.
122 experiences; 37 single executed
records with exact action and before/after frame provenance validated. Parameter strata are
fully separated; records with no actual control and failed requests are not acknowledgments
of an executed control. All source files in the individual directory retain hashes/mtimes.

Empirical status: **INSUFFICIENT_CLEAN_HISTORY**. No parameter-controlled stratum satisfies both T1 and T2 input preconditions.
Empirical T1/T3/T4/T5 NOT_EXECUTED; T2 input precondition NOT_TESTABLE where insufficient.
No empirical closure or successful empirical consumer claim is substituted with fixture output.

## Provenance and limitations

EXPERIENCE_FORMED + exact ACTION_REQUESTED/ACTION_EXECUTED + before/after OBSERVATION_FRAME
→ input CECRecord(context Node, control Node, consequence Node)
→ frozen GSC Shared with direct supports and finite roots
→ consumer follows only formed exact query/record incidence and returns all endpoint identities.
Control identity is catalog version + numeric code, with no debug action name.
Consequence identity retains baseline UnitRef/pattern_id compression; raw frames/deltas remain
provenance, and are not claimed to be complete numerical consequences.
Correspondence is temporal_association_only, not proof that the control caused the effect.

Completed engineering regressions (recorded after their executions):
- CEC-0 independent controls: 17/17 PASS.
- Frozen GSC-0/GSC-1 and FROI/interface/scheduling/checkpoint controls: 83/83 PASS.
- Existing full Python tests suite: 226/226 PASS.
These counts overlap; they are executed-suite counts, not a unique-test total.
No Minecraft or formal A was started by CEC-0. Existing regressions use isolated fixtures.
All baseline tracked files are unchanged, including formal runtime, frozen GSC and existing
standards/reports. Only the eight CEC-0 additions listed in the JSON belong to this change.
To run independent controls: `.venv\Scripts\python.exe -B -m unittest experimental.cec0.tests -v`.
The validation entry is `python -B -m debug.cec0_validation`; it refuses to overwrite the
already saved reports. Measurement commit above is the source baseline, not a claim that
CEC-0 additions already existed in that commit. The isolated implementation commit is
reported with the final delivery.

Final: **CEC0 = INSUFFICIENT_CLEAN_HISTORY**; **fixture structural validation = PASS**.
No behavior authorship, correct-control choice, parameter solution or learning claim is made.
