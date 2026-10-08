# Preserved initial verification attempts

No preregistered criterion or formation mechanism was changed in response.

1. First focused invocation without an explicit workspace basetemp: 1 passed,
   21 setup errors. Pytest could not create numbered directories in the sandbox
   package Temp root. No affected Core experiment started. Subsequent validation
   uses a new isolated .test-tmp path in the writable workspace.
2. Second focused invocation: 20 passed, 2 failed. The different-history probe
   initially used increased deltas of different magnitudes. Frozen pattern_id
   encodes channel/kind, not numeric magnitude; the two histories therefore had
   equal operative UnitRef identities. The probe now uses increased/decreased
   histories, preserving the requirement for actually different structure.
   This also records a limitation: magnitude-only changes need not change content
   identity; content is reference-based, not an exact delta codec.
   The capacity probe changed engine caps without matching the isolated state's
   locked boundary, so the correct boundary guard rejected it before construction.
   The probe now gives its isolated pair a consistent smaller budget, sufficient
   for the existing pool but insufficient for the next whole constructor batch.
   The canonical DB/caps remain unchanged.
