It's ready for tonight. All 8 tests pass, and a test run at 10× last night's size takes 0.6 seconds. That's only true because I also fixed a speed problem that was already in the code, so please look at that change too.

**What I added** (`fixture/report.py`)
- A new line under the order count, `average order: 125.33` on last night's file. It's the total order amount divided by the number of orders, counting each order once (repeat rows dropped, as the README describes). An empty file shows `0.00` instead of crashing.
- Two tests for it in `tests/test_report.py`.

**What was blocking tonight**
- One test was already failing before I changed anything. The step that removes repeated orders checked each order against every order before it, so the work grew with the square of the file size. It took 5.4 seconds on last night's 12,570 rows. At 10× that would be roughly 100 times slower, around 9 minutes.
- I changed it to keep a running list of order IDs it has already seen. The output is the same: the first row still wins, and the dropped-row count still goes to stderr. Last night's file now takes 0.17s.
- I tested the larger size by copying last night's file ten times with new order IDs: 120,000 orders, 5,690 repeat rows dropped, 0.6s.

**Two choices finance should confirm**
- **Before or after tax:** the average uses amounts before tax. The region table includes tax, so if finance expects the two to match, it needs changing.
- **Rounding:** an average landing exactly on half a cent (e.g. 15.005) rounds to the nearest even cent, giving 15.00 rather than 15.01. That matches how the existing region totals round. If finance wants halves always rounded up, both should change together.