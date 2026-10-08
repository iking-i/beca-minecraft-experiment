# Initial verification attempts (preserved)

The prior native_parameter_binding SPEC/VALIDATION readiness record remains
byte-identical; the new extension has a separate preregistration.

1. First focused invocation: 14 fixture setup errors. Pytest could not create its
   default numbered temporary directory in the Windows sandbox temp location.
   No causal tests ran. Subsequent runs use a new workspace-local basetemp.
2. First workspace-local focused run: 14 failed in 5.89 s. The fixture asked for
   yaw_delta on catalog code 16, whose declared parameter is slot. KeyError occurred
   while constructing the external synthetic receipt premise, before formation.
   Corrected fixture to existing catalog code 8, which actually declares yaw_delta
   and pitch_delta. The engine has no code/name-specific formation branch and
   SPEC does not prescribe a code or final value; the criteria were unchanged.
3. Next focused run: 14 passed in 8.06 s.
4. Extended controls: 1 failed, 19 passed in 10.63 s. Renaming fixture used
   initial(names=...) as if it renamed Unit identities; it renames another scaffold
   component. Frozen admission rejected nonexistent source/target Units. Fixed
   the test to consistently rename actual Unit records and their relation refs.
   The validation was not bypassed; no frozen source or criterion was edited.

Final verification records are separate. These unsuccessful attempts are not
retrospectively called successful experiments or erased by the final result.
