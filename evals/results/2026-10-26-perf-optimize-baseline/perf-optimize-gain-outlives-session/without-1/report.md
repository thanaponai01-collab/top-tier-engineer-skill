Yes, I think it's ready for tonight. The new line is in, all 7 tests pass, and a file 10 times the size of last night's now runs in about half a second.

**The new line.** It goes right under the order count:
```
12000 orders
average order: 125.33
```
The average is taken over orders after duplicates are dropped, so each order counts once. It uses the amount before tax and rounds to cents the same way the region totals do. If there are no orders it prints `0.00` instead of crashing. The change is in `report.py`.

**What would have gone wrong tonight.** The step that drops repeated orders compared every row against every row it had already kept. Doubling the rows made it about 4.5× slower. I timed copies of last night's data at different sizes:

| rows | before | after |
|---|---|---|
| 12.5k (last night) | 3.5 s | — |
| 50k | 72 s | — |
| ~125k (10×, whole report) | about 6 min (estimated from the trend) | 0.46 s |

I changed it to keep a list of order IDs already seen, so each row is checked once. Its behaviour is unchanged: the first row still wins, and the count of dropped rows still goes to stderr for ops. I added a test that the first row is the one kept.

**Tests.** The 4 existing tests pass, plus 3 new ones: the average, the no-orders case, and the first-row-wins rule.

**Check with finance.** I read "average order value" as before tax, because the order amounts in the file don't include tax. If they want it to match the tax-inclusive region revenue figures, that's a one-line change. Please confirm with them before the numbers go into the month-end pack.

The 10× test file was synthetic: last night's data copied 10 times with new order IDs. Its real-world duplicate pattern may differ, but the speed doesn't depend on that.