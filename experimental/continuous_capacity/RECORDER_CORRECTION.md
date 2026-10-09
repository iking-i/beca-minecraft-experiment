# External recorder correction — prior result retained

The first fresh attempt ended after E7/A13, then committed BODY_DIED A14 and
controlled shutdown A15. Its immutable REPORT.json classification FAILURE and
all database/events/raw frames remain unchanged. The immediate stop was the new
recorder's overbroad `connected=false` test, not a 64-Unit capacity failure and
not evidence that the Minecraft TCP connection had closed. BODY_DIED is real;
the cause of death is not independently established.

Actual frozen interfaces: minecraft/src/body.js observable() permits ready/dead;
EffectCore.tick() permits observation in dead state. The corrected measurement
guard follows that boundary. It does not revive the body, call respawn or grant
perform authority. The previous run cannot be called a 32-frame PASS.

Before a second fresh independent attempt, record this correction and new observer
hashes. Same original implementation, budget32, interval2 after processing, single
external bootstrap, no later interventions, no caps/state changes. No original
database or in-memory Core is reused and no old observation is replayed. This is
a repeated measurement after a recorder fault, not an automatic action retry in A.

Exception instrumentation also disables line/opcode tracing and only observes
exception-bearing recursive frames. It still propagates the identical exception;
no input/output/formation/dispatch change. Sampling intervals may exceed2 seconds
because processing and external recording take time; no exact temporal schedule
or instrument-free performance claim is made.
