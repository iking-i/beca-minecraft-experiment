# World-entry initialization audit

## Audit before modification

2026-10-04: the actual LAN server at `127.0.0.1:55005` reports Java **26.1**, protocol **775**. Installed: Mineflayer 4.39.0, minecraft-data 3.117.0. Read-only status ping showed the human player `one`, no BECA_Body. The original lifetime selection remains unchanged. The user subsequently authorized **independent new test databases**; the live acceptance uses a separately labeled test A, not the original A.

Classes: A complete existing input; B existing but defective/overabstracted; C missing basic input; D conditional input; E outside ordinary current-world participation; F carrier limitation. These are audit findings, not a claim that every native GUI has been implemented.

| Native interaction | Before | Evidence / reason |
|---|---|---|
| Forward/back/strafe, look, jump, sprint, sneak | B | `body.move` clears other keys before/after timed motion. No independent sustained press/release. |
| Swimming/climbing | C/F | Ordinary key combinations missing; water/ladder physics depends on installed prismarine-physics, not an exploration policy. |
| Dig/start/cancel/finish | B/C | `bot.dig(...,'ignore')` still runs a timer and `_updateBlockState(...,0)` locally; formal cancel unavailable. |
| Place and block use | B | Place implicitly equips a selected inventory slot; block use hardcodes top face/center/main hand; reach check alone does not check sight. |
| Attack/entity use/mount | B/D | Opaque refs exist; sight not checked; no independent offhand use input. Mount is a possible server consequence of entity use, not a guaranteed action result. |
| Dismount | C/D | No explicit release-from-vehicle input. Installed `bot.dismount` sends jump on modern protocol, which is not the protocol's shift input. |
| Vehicle steering/boat motion | F | Mineflayer disables walking physics on mount; sending input bits alone does not implement boat/client vehicle physics. |
| Hotbar and arm animation | A | Explicit slot/swing, no best-item selection. |
| Main/offhand, held-use/release, hand swap | C | Main-hand timed use only; slot 45 visible but independent use/release absent. |
| Drop/equip/slot transfer | B | Exact parameters, but transfer/equipment routines fold multiple clicks. Native raw click exists only for mode 0. |
| Left/right click, cursor, container slots/close | A/B | Slot state supplied; predicted slot changes are distinguishable from subsequent server feedback, but local model is not server acknowledgment. |
| Shift/number/drop slot clicks | C | Installed window model supports modes 1/2/4. |
| Drag/double click, offhand number-key swap | F | Installed prismarine-windows drag/double implementations throw `unimplemented`; number swap validates only 0..8. |
| Personal 2x2 and workbench 3x3 | A/B | Actual slot layouts exposed; result-transfer macro combines clicks. No recipe lookup/craft call. |
| Furnace/container varieties | D | Generic observed window slots operate without container-purpose knowledge. Window properties/progress are incompletely exposed. |
| Anvil/enchantment/trade selection | D/F | Slots alone do not carry name/button/trade selection or offer/property feedback. No faithful dedicated channel yet. |
| Books/sign editing | D/F | Missing text/editor-state/commit channels. Do not pretend block-use implements text entry. |
| Bed/sleep/wake | D/C | Bed use must be ordinary block input and server decides sleep; no wake input. `bot.sleep` would aim automatically and is excluded. |
| Manual respawn | C | Mineflayer default auto-respawn supplies a decision, while `observe`/Core tick reject dead state. |
| Creative flight, command/operator UI | D/E/F | Permission/game-mode specific, not ordinary survival startup; flying/native creative editing not validated. Operator/world-control commands are outside A's body. |

## Startup blockers identified

Sustained independent keys; opaque numeric formal codec; hand-use/release; explicit dig lifecycle without fabricated world updates; removing implicit equipment/slot macros from the formal path; target/view/face validation; death observation/manual respawn. Dismount and wake are necessary conditional releases. Advanced editors/vehicle physics remain explicit conditional blockers if those world states enter the experiment.

Implementation, tests and live acceptance results follow below. Fixed body provisioning is external BODY_CAPABILITY, never learned structure. Recursive code, sampler preference, capacity locks and original identity/database/history are unchanged. User-authorized independent test histories append normal engine events without rewriting prior rows.

## Implemented corrections and precise boundaries

| Original blocker | Actual implementation / code | Result |
|---|---|---|
| Timed motion erased other keys | `body.move`, `native_inputs.setInput`, 34 | Independent held controls; timed aliases restore only their own keys. Death/retirement clears inputs. Modern packets carry the complete mask. |
| Human action labels reached A | `formal_command`, `provision`, `FrameEncoder`, numeric `capabilities.perform` | Numeric request/results and control IDs; human action labels and requirement descriptions stay outside the formal frame/registry. Numeric errors return reason code, not usage hints. |
| Hand use/release missing | 35/36/46; session.useHand vs bot.usingHeldItem | Main/offhand input, release, swap; requested hold state is distinct from server use state. Server rejection of empty-item use does not prevent explicit release. |
| Predicted world edit and no cancel | 14, 37/38/39; `startDig`, `endDig` | Raw dig packets; no `bot.dig`/`_updateBlockState`. 14 retains native-duration alias; separate inputs leave timing to the caller. Only actual world updates change observed blocks. |
| Implicit equip / multi-click goal folding | 15 guard; 19/20/21/25/26/27/30/31 formal_enabled=false; 43 | Held-slot mismatch fails without equip. Eight macros remain debug compatible; formal calls refuse them. Supported raw native slot modes are independently available. |
| View/face ignored | `blockHit`, `entityHit`, 15/22/23/24/44/45 | Current collision ray / face / point / entity bounds and occlusion checks; no aim, approach, alternative target or retry. Hit refs/points are numeric/opaque sensor data. |
| Death inaccessible / automatic respawn | createBot(respawn=false), observable(), 40, Core.tick dead-state gate | Death remains observable. Only explicit input requests client respawn. Existing selector/engine unchanged; conditional availability is not a survival reward. |
| Cannot leave ride/bed | 41/42 | Shift input for dismount; correct modern stop_sleeping packet. Installed Mineflayer `dismount` jump and `wake` legacy actionId=2 are bypassed. No fabricated vehicle/sleep consequence. |

ActionSpace v2 has **47 definitions**, **39 formal-capable entries**, and **8 retained debug-only macros**. New codes are 34..46. Death currently exposes only the manual respawn input; the existing fixed sampler choosing that sole available input remains EXTERNAL_FIXED_POLICY, not autonomous survival strategy formation.

The raw observation/auditor log and compatibility snapshot still contain human diagnostics; they are not the recursive input or parameter-binding source. The actual engine receives FrameEncoder output, and provisioning stores the sanitized definition. This is a boundary claim about executed access paths, not a claim that every stored byte is numeric.

### Conditional capabilities / carrier limitations

- Water/ladder movement uses normal controls and installed physical simulation; **not live-validated** here. Do not infer swimming/climbing knowledge from capability installation.
- Entity bounding-box ray checks are a bounded carrier approximation. Special hit shapes, collision margins, attributes/modded interaction ranges, client GUI input capture and creative input behavior are not fully modeled/validated. Default block ray 4.5 (creative 5), entity ray 3 (creative 5) additionally retains the previous bridge's entity-center 3-block guard. This can be stricter than a native creative player.
- Mounted controls are not complete vehicle/boat physics. Mineflayer disables walking physics on mount. Dismount is provided; steer bits are **not** claimed to reproduce client vehicle motion.
- Raw slot input supports modes 0/1/2/4. Installed prismarine-windows `dragClick` and `doubleClick` explicitly throw `unimplemented`; modes 3/5/6 return **CARRIER_LIMITATION**, not an invented action or substituted click. Offhand number-key swap beyond model button 0..8 is also limited; ordinary offhand slot clicks and explicit hand-swap remain available.
- Inventory/window slots are Mineflayer's current, possibly predicted view. `slot_feedback_kind=0` and actual inventory synchronization packet counter are exposed. No per-click server acknowledgment is claimed. Specialized GUI properties/progress, trade offers/selections, enchant buttons, anvil names and text-editor state/commit channels for books/signs remain conditional limitations. Slots alone do not implement these interfaces.
- Bed entry is ordinary block input followed by server acceptance/rejection, not `bot.sleep` with hidden aiming. Wake, respawn and dismount positive server consequences remain conditional validation gates.
- Flight/creative edit/operator commands are not silently added. Commands/world editing are experimenter authority, not A's bodily knowledge.

These limitations are not evidence of failed learning/recursion. Choosing targets, timing, interpreting effects, using tools, recipes, trade conditions and action combinations are not pre-solved by the body. The existing external finite-domain sampler does not guarantee suitable continuous coordinates or discovery; its expressiveness/authorship is a separate task, not a claimed learned policy.

## Tests

Final full suites: **Python 123 tests** and **Node 42 tests**, all passing. JavaScript syntax checks also pass. Node transport tests use actual Mineflayer against a closed local port and a deliberately unsupported protocol server, not the live world. Protocol tests serialize raw block/entity/shift/swap/dig/wake packets with the installed **26.1** serializer.

Tests cover every new definition's schema/availability or conditional state, successful input and true failure, stale references/windows, held input preservation/release, no auto equip/retry/retarget, no fabricated air update, death observation and explicit respawn through normal Core.tick, numeric knowledge boundary and TEST_ONLY/external provenance. Existing macro compatibility tests remain separate from formal refusal tests. Environment doubles explicitly supply block/window consequences; they are never imported into the real body.

## Live Minecraft acceptance — partial, not blanket validation

User-authorized independent test individual: `A-6cf87532-49e5-421d-ac7d-c7c353c537b1`, database under its own `storage/individuals/<id>/` directory. Original selection remains `A-9ea5abde-7fa2-4313-a102-254d4664fd49` at **A14828**, condition `C-14cfeffb-7076-4f78-bf61-4c799a169f92`; it was not opened for runtime or reset.

Two acceptance Sessions retained in the test lifetime, **A0..A134 / 135 snapshots**, not merged into the original A. The second Session `S-0800ad1c-f154-40d7-bac3-b4d75488fa17` added 14 requests: **10 sent/executed, 4 honest failures**, plus 16 renewed observations. Every explicit action's decision authorship is **TEST_ONLY**.

| Live chain | Actual evidence |
|---|---|
| Held movement / release | Source A77 -> code34 press -> renewed observation A81 at (737.7,69,120.610825...); source A81 -> release -> A84 at (737.7,69,121.074202...). Continued displacement while releasing is physical inertia, not a substituted action. |
| Offhand start / release | Sources A84/A88 -> codes35/36 -> renewed observations A88/A92. Both inputs succeeded after the empty-use release correction; no item consumption is asserted. |
| Hand swap | Sources A92/A96 -> two explicit code46 inputs -> A96/A100. Input and inventory packet feedback recorded; not claimed as an independent item-use skill. |
| Aim / dig start / cancel | Explicit code13 look; source A106 -> code37 -> A109; source A109 -> code38 -> A113. No automatic target switch or dig completion. |
| Block-hand input | Source A113 -> code44 explicit offhand/face/hit coordinates -> A117. Sent and re-observed; no claim that it opened a container or placed a block. |
| Invalid state / stale ref | Codes41/42/40/44 -> NOT_MOUNTED / NOT_SLEEPING / INVALID_STATE / INVALID_REFERENCE -> observations A121/A125/A129/A133. No recovery substitute or new identity. |

The first Session's report retains the auditor's missing process_id comparison error and the initial empty-use release failure; neither was erased. The second report proves `individual_id_preserved=true`, `boundary_preserved=true`, `prior_snapshot_unchanged=true`. The existing Supervisor can classify Bridge closure during normal worker shutdown as bridge_process_exited although worker exit is 0; this monitor race is retained in audit logs, not misreported as a Minecraft action failure or changed by this task. The experimenter runner uses worker exit/report for acceptance status.

Local evidence: `reports/world-entry-validation.json` (first attempt) and `reports/world-entry-validation-1791107473048431500-1e0077d3.json` (second attempt), plus append-only action/state events and separate supervisor_events. Runtime databases/reports remain ignored by Git. Reproducible experimenter runner: `python -m debug.world_entry_validation --new-test --port <port>`; repeat an existing test A using its separate --selection file.

**not live-validated**: manual respawn positive path (user chose not to test death), positive sleep/wake/mount/dismount, swimming/climbing, real GUI slot effects, explicit completed dig / actual placed-block or consumed-item effects, and real entity input. Unit/protocol tests do not upgrade these to live claims. No destructive death injection, teleport, pathfinding or automated equip was used.

## Startup decision

The bounded **ground movement / input / honest consequence / renewed-perception loop runs in the real world**, and identified basic interface defects have been corrected. **Full ordinary-player causal World-entry acceptance is not yet complete.** Remaining gates are positive live validation of the above untested foundational/conditional consequences, and faithful channels for the listed carrier limitations when those states occur. Do not declare unrestricted Minecraft participation, learned behavior, V0-C, architecture recognition, L1 or upward recursion from these results. This task stops at the documented body boundary; it does not prescribe solutions to A's future problems.

## Changed files

| Area | Files |
|---|---|
| Native body and catalog | `minecraft/action-space.json`, `minecraft/package.json`, `minecraft/src/body.js`, `minecraft/src/capabilities.js`, new `minecraft/src/native_inputs.js` |
| Core boundary / codec | `individual/action_space.py`, `individual/observation.py`, `individual/core.py` (dead-state body scheduling only) |
| Tests / doubles | `minecraft/test/body.test.js`, `minecraft/test/capabilities.test.js`, new `minecraft/test/world-entry.test.js`, `minecraft/testing/capability_bot.js`, `tests/fixtures/capability_body.js`, `tests/test_action_space.py` |
| Experimenter-only live acceptance | new `debug/world_entry_validation.py` |
| Documentation | new `WORLD_ENTRY_AUDIT.md`, `BODY_CAPABILITIES.md`, `EXPERIMENTAL_IMPLEMENTATION_BOUNDARY.md`, `README.md`, `VALIDATION.md`, `VALIDATION_STAGE3.md` |

The previously authorized missing-lifetime initialization fix in `individual/lifetime.py`, `individual/storage.py`, `tests/test_storage.py`, `LIFETIME_STORAGE.md` is preserved as a separate preceding commit, not a recursion/body behavior change. Its README explanation accompanies the current documentation update. Real configuration, original selection, databases, logs and reports are not staged.
