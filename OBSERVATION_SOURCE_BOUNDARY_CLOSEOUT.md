# Observation Source Boundary — TEST_ONLY closeout

Date: 2026-10-09. Branch: `codex/operative-connection-correction`.
Baseline: `f2d66102755038dad688a20189767ded24651b0e`.
Implementation/validation: `96ec13158531f4e521d611694f587dbb46015d2f`.
Closeout anchor: the separate commit adding this document and its handoff.

**OBSERVATION_SOURCE_BOUNDARY_TEST_ONLY = PASS / COMPLETED / FROZEN**,
strictly for the supported storage/reference/continuation scope below.
This does not change the original two-part real protocol from PARTIAL to PASS.

## Frozen question and mechanism

Can complete verifiable observation sources remain authoritative, independently
of optional Full Audit History, without embedding every historical body in active
InternalState or changing the tested lawful ordinary recursion/reference results?
The preregistered OS-T1–OS-T10 remain in `experimental/observation_source_boundary/SPEC.md`.

Only the explicit isolated `BoundaryCore` lifecycle is accepted. The same lifetime
SQLite database contains `os_boundary`, immutable `os_sources`, `os_atoms` and
`os_channels`. Source bodies, exact incidence indexes and archive head are flushed
inside the existing Current State transition transaction; a failed transition
rolls them back together. Sources are not optional audit events/snapshots.

InternalState retains an archive descriptor, Unit-to-frame incidence, the complete
current source register and the existing bounded observation window. Exact indexed
ObservationRef/ObservationFactRef access validates frame/channel/digest, namespace,
ambiguity and current object epoch/membership. Decoded source cache is limited to
eight and cleared at observation boundaries. No historical body is deleted for
being unused. Source and index disk usage can continue to grow.

## Separate evidence layers

| Evidence | Actual result | Scope |
|---|---|---|
| Offline saved E1–E32 | OFFLINE_PASS; OS-T1–OS-T10 PASS | Representation comparison in independent diagnostic databases; not live replay |
| First real attempt | PARTIAL, four OFF frames | Body died; original raw evidence retained; ON never began |
| Second real attempt | PARTIAL, eight OFF plus one ON frame | Normal resumed carrier epoch gap was recorded; original recorder stopped |
| Third Session supplement | PASS_FOR_THIRD_SESSION_SUPPLEMENT, eight ON frames | Same second-attempt A/database resumed from A19; initial epoch gap followed by seven lawful within-epoch experiences |

These are not a continuous sixteen-frame Session or a completed original 8+8
protocol. Preliminary recorder-module failure and connection EACCES remain
NOT_TESTABLE records; initial implementation/control failures remain preserved.

The first real individual was `A-d5b960f4-ba3d-44b2-a6bc-a94096fe17e7`:
E1–E4 formed three experiences/integrations, last observation A8, death A9,
normal close A10. Its four sources and original database are preserved.

The second attempt and supplement share
`A-87cd4a08-65a3-4d51-81ad-49b00343e8a4` and one unchanged database identity:

| Session | Mode / Core PID | Frames | Experiences / integrations | Normal close |
|---|---|---|---|---|
| S-fc03952a-906e-43f0-94cb-7b4a82309dd0 | OFF / 28160 | E1–E8, A5–A12 | 7 / 7 | A13 |
| S-47fcc6f7-e2a0-4097-a498-96853d34f4ac | ON / 34260 | E9, A18 | 0 / 0 | A19 |
| S-bb0d19b9-db2f-4dfd-9962-15a39b668706 | ON / 36376 | E10–E17, A24–A31 | 7 / 7 | A32 |

The third process restored A19 as session state A20 without reconstructing A,
replaying optional history or replacing its internal structure. The old nine
source rows were unchanged. Normal epoch changes 0→1 and 1→2 produced explicit
TEMPORAL_LINK_UNRESOLVED at E8→E9 and E9→E10, with no fabricated cross-epoch
experience. E11–E17 resumed ordinary experience/integration and an ACTIVE
recursive process. The supplement changed only the external recording stop rule:
continue across the expected first-frame gap, still stop on genuine body/transport
failure. It did not change recursive formation, persistence or execution rules.

All live frames preserve 376 numeric channels, 64 object references and 47 body
capabilities. OFF saved eight authoritative sources with no optional observation
events; the audit gap remains A0–A13 and ON snapshots begin A14. No OFF history
was backfilled. At A32 all seventeen sources audit successfully. Exact E1 numeric
FactRef probes resolve in the new process; these labelled external probes are not
A's recursive input. Runtime access logs separately record ordinary historical
dependency reads. Neither is evidence of Pair reuse: the latter runs contain zero
Pair nodes. No perform, sampler, binder, respawn or world intervention occurred.
Peaceful difficulty was supplied by the experimenter, not formed by A or measured
by an interface that does not expose difficulty.

## Resource evidence and nonclaims

Offline equivalent InternalState: 236,219→1,247,906 bytes in the frozen
representation, versus 185,312→270,011 in the new representation; E16–E32 is
270,011 bytes in this fixture. Final charged structures remain 31/64. Offline
sampled peak RSS did not decrease: 66.902 versus 68.293 MiB. Timings are recorded
but not a dedicated benchmark (instrumentation, fixture loading and commit scope
differ); serialization shrinkage does not prove RAM boundedness.

The third live Session finished with five Units, zero Pairs, three typed
connections, charged capacity 5/64 and relation charge 12/96. Seventeen source
bodies total 433,942 bytes. InternalState E10–E17 was 204,494→214,896 bytes;
final whole Current State JSON was 337,793 bytes. Worker RSS initial/peak/final
was 30.445/53.781/46.906 MiB. Late ordinary cycles decoded seven source bodies,
178,682 bytes per measured cycle, without loading all seventeen. Twenty-one
nonfatal current limits (observation history 8, condition channels 7, evidence
references 6) were consumed; no capacity increase occurred. These finite samples
do not establish long-run state, total RAM or source-disk bounds.

**Known semantic difference:** frozen validation checks all historical bodies each
cycle; this version checks archive boundary and actually accessed dependencies,
with all-source/index checking in explicit external audit. Unaccessed corruption
may be detected later. The control permits an ordinary cycle with unrelated
corruption, then rejects direct access and full audit. Lawful-data witness
equivalence is supported; malformed-history detection-time equivalence is not.

- Original 8+8 protocol: PARTIAL, unchanged.
- Real cross-process Pair reuse: NOT_ESTABLISHED.
- Long-term overall memory boundedness and unlimited running: NOT_ESTABLISHED.
- Default/formal A adoption: NOT_ESTABLISHED; no migration or default enablement.
- Purpose, need and structure unloading: NOT_IMPLEMENTED.
- Autonomous behavior, new world causal law, L1 or complete theory proof: not claimed.
- Existing independent body-loop results remain frozen; no new body loop is claimed here.

## Verification and evidence anchors

Saved logs, checked during closeout, record **21 focused**, **88 related**,
**784 full regression / 114 subtests**. These executions predate closeout and
the later real recorder; no tests or experiments were rerun for this closeout.
Overlapping sets are not summed. Earlier 781-test collection remains historical.

Thirteen LF-normalized frozen hashes match; 512 protected old files and 27
unrelated files match their preserved anchors. Existing evidence hashes and the
first/final real database digests match; the second report's database digest is
a historical A19 snapshot, legitimately superseded by the authorized A32
continuation. No old report or historical SHA was rewritten.

Raw `git diff --check` for the implementation detects original trailing whitespace
in CHANGED_FILES.md, the raw ISOLATION.patch and FULL_FINAL.txt. Their original
bytes are retained. All other implementation files and new closeout documents
pass the whitespace check. This is not a new test failure or a modified mechanism.

`experimental/observation_source_boundary/CLOSEOUT_VALIDATION.json` records the
layered results, verification scope and complete artifact/hash inventory.
`evidence/live_raw_export/MANIFEST.json` anchors exact compressed raw frame,
pre/post-state, transition, transport, RSS and original failure/run records.
No database, private settings, credentials or unrelated file is committed.

Current index only: README and RESEARCH_STATUS.md/json are updated. Theory
reference and all previous frozen results remain unchanged. **NEXT_PHASE =
NOT_STARTED**. No next-stage design, implementation or Minecraft execution is
authorized by this closeout.
