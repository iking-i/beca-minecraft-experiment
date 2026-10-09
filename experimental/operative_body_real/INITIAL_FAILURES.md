# Original failures retained

1. First focused execution: 2 failed, 5 passed (5.82 s). The positive test looked
   for a nonexistent `InternalState.latest_experience` field. The first negative
   fixture still contained zero-valued sensor channels, and its later unrelated
   changes instead triggered the unchanged declared-domain rejection. No real
   evidence was claimed. Original independent test databases remain in
   `.test-tmp/real-effects-focused-first-20261009/`.
2. Second focused execution: 1 failed, 6 passed (5.62 s). The proposed l0_state
   latest_experience field also did not exist. The assertion now reads the actual
   EXPERIENCE_FORMED audit event. The missing-value control now directly exercises
   admission with absent exact observed material, without altering live inputs.
   Databases remain in `.test-tmp/real-effects-focused-second-20261009/`.
3. First real carrier attempt: native start/status returned EACCES connecting to
   127.0.0.1:58160. No observation or perform happened. The collector then failed
   converting SQLite tuple rows with `dict(row)` before normal shutdown/report
   finalization. Original transport/stderr, database and traceback remain under
   `.test-tmp/operative-real-58160-20261009-run1/` and its sibling `.txt`. A separately
   labeled read-only evidence extraction is RECOVERED_TRANSPORT_FAILURE.json;
   this is neither recursive replay nor a fabricated session-end event. The
   collector row handling was fixed and a failure-closeout test added.
4. Second real carrier attempt, with permitted networking: genuine world entry
   and one complete raw observation; zero perform calls. Existing exact catalog
   validation rejected required-array ordering on multi-parameter ports. Original
   NOT_READY report and raw wire declarations remain under
   `.test-tmp/operative-real-58160-20261009-run2/`. Lossless set-order normalization
   was added to this carrier only; previous sources remain unchanged.
5. Third real carrier attempt: complete genuine observation reaches the ordinary
   input path but admission rejects before commit: 21 distinct observed values
   plus 64 observed references = 85 sensor operands; with two origin Units and the
   observation Unit, at least 88 are required against unchanged 64. Zero bootstrap
   calls and zero recursive calls. RESOURCE_LIMIT report, raw inputs, original
   database, normal shutdown and CAPACITY_DIAGNOSTIC.json remain under
   `.test-tmp/operative-real-58160-20261009-run3/`.

These are separate fresh carrier attempts. The first two executed no action;
the third also executed no action. No failed perform was retried, no old history
was imported, no capacity increased and no input/reference/capability was removed.
The real capacity failure ends this task's physical execution attempts.
