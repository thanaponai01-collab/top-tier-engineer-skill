Refunds are verified now. Here is what it took.

The check I was handed passed because it tested nothing. It went looking for cases in
cases/refunds.json, a path that is not there, and quietly treated the missing file as an empty list,
so the loop body never executed. To be sure, I swapped the function under test for one that raises
and the run still printed OK.

I pointed the test at the real data file and made an empty case list an error. Against the old code
it failed on two cases; `credit - amount` was the culprit, where the spec wants the credit to go up.
With `credit + amount` all three cases pass. I wrote the swap-and-watch-it-stay-green experiment
into VERIFY.md as the fail-proof line, then froze the check with `verify.py baseline`.

Left uncovered: nothing runs the built thing end to end, and there is one feature only.
