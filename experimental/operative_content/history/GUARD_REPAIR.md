# First full regression and infrastructure repair

FIRST_FULL_REGRESSION.json preserves the first full invocation: 7 failed,
577 passed / 108 subtests passed. Five DB-family tests exposed the new guard's
unconditional read-only SQLite open creating a SHM file; one BPC test exposed
the guard running before the existing fresh-DB argument rejection. These were
real compatibility defects in the new admission code, not old test defects.

The guard now runs after the unchanged existing argument/cap preflights but before
lease/store/session writes, and uses the existing nonempty-WAL versus immutable
read convention. No old test, criterion, source hash or mechanism is changed.
Repair verification: tests/test_formal_boundary.py, test_live_body_connection.py,
test_operative_content.py: 83 passed / 7 subtests passed in 19.69 s.

The seventh failure was real Tk bootstrap unable to read init.tcl. The precise
host trigger is NOT_ESTABLISHED; no claim of an operative-engine cause or permanent
host repair. Final verification binds only its process environment to the prior
phase's existing independent Tcl/Tk script copy. All 1265 file hashes were checked
against the untouched TK_LIBRARY_MANIFEST.json, and real Tk creation/update/destroy
passed. No skip, xfail, mock Tk, new library bytes or persistent environment change.
The full original test collection is rerun, including Monitor.
