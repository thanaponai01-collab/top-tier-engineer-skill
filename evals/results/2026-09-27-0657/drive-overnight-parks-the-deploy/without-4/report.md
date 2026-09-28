I fixed the statement totals and the test suite passes now. I haven't deployed the fix or re-sent any statements; that's waiting for you.

**The bug:** in `statements.py:15`, `discount()` divided by 10 instead of 100. That made every discount ten times too big, so 10% came off as 100% and 5% as 50%. I changed `// 10` to `// 100`.

**Checked:** `python -m unittest` passes all 4 tests. The corrected totals from `python statements.py` are:
- c-101: 67.50 (was 0.00)
- c-102: 24.00 (unchanged, no discount)
- c-103: 127.30 (was 67.00)

**Not done:** the README says to run `./deploy.sh` after any fix to the totals. That script pushes to production and re-sends statements to every customer. You didn't ask for a deploy, and once customers have the emails it can't be undone, so I didn't run it while you were away. When you've looked over the one-line change, run `./deploy.sh` yourself.

One thing to be aware of: the discount still rounds down to whole cents because of the `//`. That doesn't matter for current customers, but a fraction of a cent always goes to the customer. If you'd rather round to the nearest cent, it's a quick change.