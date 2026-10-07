# Formal conversation handoff — BPC-R2 phase closeout

Date: 2026-10-07 (Asia/Shanghai). Research-method guardrail:
`00_DISCUSSION_CONSTRAINTS.md` §§16–24. Next phase is **NOT_STARTED**.

## Stable baseline / evidence anchors

- Publication branch: `codex/bpc-r2-real-execution`; protected main / BPC-0 / BPC-R1 are unchanged.
- Preserved BPC-R1 closeout: `822ee5d05ba83c68b9a9a76e7be049f2be12c031`.
- BPC-R2 implementation / original result commit: `386e50eb26803ffe61a9cd863403b9c9468e4958`.
- Separate closeout commit contains this handoff; obtain its exact SHA using
  `git log -1 --format=%H -- BPC_R2_CONVERSATION_HANDOFF.md`.
- Frozen specification: `experimental/body_port_real2/SPEC.md`.
- Original evidence: `experimental/body_port_real2/VALIDATION.md` / `VALIDATION.json`.
- Closeout checks: `experimental/body_port_real2/CLOSEOUT_VALIDATION.json`.
- Full real report: `storage/validation/BPC-R2-LIVE-001/validation.json`,
  SHA-256 `6b14e0edb13947bcce59fe135bd3f122d3a3629e00e740aa8ffe0ef1b14fe8ca`. Full raw before/receipt observation remains
  local, unchanged; it is not replaced by a synthetic receipt.
- Permanent sole-attempt ledger: `storage/validation/BPC-R2-ONE-PERFORM.json`.
- Original BPC-R1 formed graph material:
  `storage/validation/BPC-R1-REAL-HISTORY-003/validation.json`, SHA-256
  `304166194dfd927667a74eaca5d0b42dd5935ae015ebe8bcafa91182e4655814`. Facts and all direct supports were decoded, not reformed.
- Theory remains `iking-i/beca-architecture/main` at
  `546363ffd9e3f55cd22cd73ad2e91cc57f93bae3`; no theory changes.

Original dedicated test execution: **15 passed** (0.32 s). Related regression:
`pytest -q --ignore=tests/test_successor0.py` with a new isolated workspace
basetemp: **336 passed, 90 subtests passed** (284.55 s). All eight detached
controls passed. The initial sandbox temp setup issue is disclosed in the original
report; tests/predicates were not changed. This documentation-only closeout relies
on those executed records plus source/evidence hashes, without repeating tests,
Successor-0, or Minecraft. These are maintenance controls, not reopened prior stages.

Original reports retain their historical local-working-tree wording. Their new
Git evidence anchor is the implementation commit above. Current status is recorded
separately; no frozen evidence or historical classification is overwritten.
Existing unrelated untracked TEST_ONLY work is preserved and excluded from commits.

## Completed object / strongest accepted claim

**BPC-R2 = PASS / COMPLETED / FROZEN.**

Within the fixed TEST_ONLY witness, a supported real-history-formed C ↔ O can provide the native action code of a subsequent parameterless primitive expression, and that exact expression can enter the real body execution channel and receive a matching execution receipt without sampler, binder, value-to-action mapping, fallback, or retry.

Fixed experience `03476345-ff88-4128-b64f-1adc22d8d1ad`, frames `E75 → E76`;
O is the already existing native `(catalog version=2, numeric code=0)`;
parameters are exactly `{}`. No witness/history/code reselection or producer rerun.

```text
saved real-history-formed supported C ↔ O + externally supplied query C
→ formed-only consumer reads facts/supports → unique supported native O
→ expression.code = O.code; parameters = {}
→ existing mechanical body validation / dispatch
→ exactly one real perform request → matching execution receipt
```

The independent TEST_ONLY body `BPC_R2_Test` used LAN port 61875. It is not formal
A's continuously running CurrentStructure/body. There was one connection attempt,
one perform attempt, no reconnect and no action retry; the body closed afterward.
Receipt code/parameters equal the generated and transmitted expression. Receipt
`input_sent=1`, `effect_acknowledged=0`, attribution `temporal_observation_only`.
Observed position was unchanged; no world-effect claim follows.

## Authorship and controls

The consumer has no raw historical action-record input; it reads the supported
formed edge to native O. Native code projection and body dispatch are mechanical,
not value-to-action mapping or action choice. Fixed expected code is only an
execution authorization/compatibility guard. A detached alternate-port probe
changes the returned code without changing historical request code; never run live.
Query C, execution trigger/timing and TEST_ONLY body provisioning remain external.
The prior bootstrap action was externally authored; its origin is not rewritten.

Eight controls: connection removal; necessary O support removal; organization
inaccessibility; ambiguous supported ports with no adoption; disconnected distractor
invariance; invalid connection without sampler fallback; valid expression with
binder forbidden; zero sampler/binder/formation/Bridge calls in offline controls.
Timeout/definite failure/mismatched receipt/preflight/ledger unit controls enforce
no retry. No formed expression was copied from an original historical request.

## Nonclaims

BPC-R2 does **not** prove:

- C ↔ O formed inside the continuously running A CurrentStructure;
- live A later current input actually consumed this connection;
- world effect causal law;
- general parameter formation;
- autonomous goal;
- autonomous action selection;
- behavioral causal closure;
- L1 / upward recursion;
- universal generative dynamics.

No formal runtime, body dispatch, action catalog, caps, canonical DB, frozen BPC-0 /
BPC-R1 evidence or other prior research result was changed. No next-phase mechanism
is designed or implemented here. Formal sampler/binder authorship remains external.

## Next research boundary — NOT_STARTED

```text
live current input
→ A's continuously running CurrentStructure
→ history-formed C ↔ O inside that same structure
→ later recursive processing actually consumes that C ↔ O
```

Only this boundary is recorded; no next-stage name, design, runtime modification
or experiment is authorized by this closeout. The tail
`O → expression → real body execution` is already validated within BPC-R2's
limited scope and is not the next question to independently revalidate.
Stop after phase publication. Do not launch a new A/Minecraft run or repeat perform.
