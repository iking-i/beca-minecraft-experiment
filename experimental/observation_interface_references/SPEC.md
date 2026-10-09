# Complete observation references — isolated TEST_ONLY repair

Baseline: eb94318242b42843e0ec12c0b40b96751c563dc9. No prior result changes.

The question is whether full real observation facts can enter the same ordinary
Core state chain without materializing every external fact as an internal Unit.

Before validation: accept only complete catalog and observation provenance.
Store lossless sensor sources with frame identity, namespace, epoch, every channel,
all object tokens, timestamp and sequence. ObservationRef denotes an exact typed
value/object identity backed by those sources, not a channel-equivalence claim.
ObservationFactRef additionally addresses one exact source/frame/channel.
Equal scalar identities retain distinct channel/frame evidence. EffectRoute still
requires its exact channel and actual change/supports. Old object references must
be observed in the current epoch/scope; stored numeric facts can be historical
construction material, but native receipt incidence requires current membership.

Acceptance: saved actual sample retains 376 channels, 64 object references and
47 declarations; ordinary observation commits without eager sensor Units; later
ordinary hooks construct and reuse referenced content; invalid references, wrong
channels/sources, stale objects and actual internal over-capacity reject. Existing
formation, native incidence, ablation and cross-process reuse remain causally
valid. All actual Units, content leaves/Pairs, cells and effects retain64 shared
capacity; actual relations/routes retain96. External facts have no execution
authority and are not fake Units. This change does not establish bounded growth
of the external-source register or a real loop.

Offline replay of the saved real sample is explicitly separate from live evidence.
Live verification uses a fresh DB/A, port confirmed by user, no imported history,
one labeled external bootstrap {code:16,parameters:{slot:0}}, unchanged8-observation/
30-second window, no sampler/binder/retry/planned future actions. New observations
alone may activate already formed routes. Missing actual recurrence is NOT_READY;
actual structure limits are RESOURCE_LIMIT; unavailable world is NOT_TESTABLE.
No FakeBridge result substitutes for Minecraft execution or world causality.

Only this package and its independent tests/reports may change. No commit/push.
