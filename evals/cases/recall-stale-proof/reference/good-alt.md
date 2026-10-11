Where things stand: the notes say the export is finished and proven, but that's out of date.

I reran the tests and they fail. Two of three are red because 10.125 now rounds to 10.12. The last
commit (Oct 9, "money: use standard rounding") changed money.py to banker's rounding (ROUND_HALF_EVEN).
BRIEF.md records that the owner and accountant chose half-up rounding to match the PDF invoices. So
that commit broke an agreed requirement, and the fix is to put half-up back, not to change the tests.

There's also uncommitted work: export.py has a new `since` argument passed through, but the actual
date filter is only a TODO comment. It's half-built.

Suggested next step: revert the rounding change in money.py and rerun the suite until it's green,
then continue the --since filter. BUILD.md's "DONE, proven" line needs updating after that.
