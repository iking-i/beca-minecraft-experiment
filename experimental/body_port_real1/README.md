# BPC-R1 — real-history formation only

Independent TEST_ONLY offline adapter. Research question and pre-registered
criteria: [SPEC.md](SPEC.md). Frozen BPC-0's `form` is imported unchanged;
its synthetic input codec and expression consumer are not used.

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_body_port_real1.py -q
.\.venv\Scripts\python.exe -m experimental.body_port_real1.validation --output storage/validation/BPC-R1-NEW-MEASUREMENT
```

Output must be a new directory; previous measurements are never overwritten.
SQLite is opened read-only. Existing real formal history is the source, not unit
fixtures. Full canonical evidence, formed facts, all direct supports, source
identities/digests and rejection reasons are saved in the machine report.

RealExperience keeps native port identity, action identity/status, actual receipt,
two actual ObservationFrames, raw observations and formal history provenance.
It preserves finite floating-point sensor values and coverage changes rather
than coercing them to the old integer fixture. Existing semantic diagnostic text
remains opaque evidence and has no role in formation or selection.

Generic record incidence forms `Shared(C,O)`; the read-only verifier returns
all supported ports, reports ambiguity, and never constructs a body expression.
No `perform`, sampler, binder, Minecraft connection or runtime writes occur.
Source authenticity is bounded by trusted pre-existing local formal records;
this does not establish adversarial sensor/receipt authentication.
