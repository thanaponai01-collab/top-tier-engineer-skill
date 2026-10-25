The report is now fast enough for next month's export, and its output is byte-for-byte the same as before.

| | Before | After |
|---|---|---|
| Last night's export (12,570 rows) | 1.55 s | 0.15 s |
| Test export 10× bigger (~125,700 rows) | **5 min 32 s** | 0.47 s |

The old version wouldn't have fit in your window at all. One of the two slow parts grew with the square of the row count, so ten times the data took about 200 times as long, not ten.

**What I changed (two small edits):**
- **`report.py`, `dedupe`:** removing repeated orders checked each order ID against a list of every ID seen so far. It now uses a set, which checks in one step. The first row still wins, and the rows stay in the same order.
- **`regions.py`, `_table`:** `regions.csv` was opened and re-read twice for every order to look up a tax rate and a name. It's now read once and kept in memory (`@lru_cache`).

**Why no figure can change:** the money calculation is untouched. It's still exact decimal arithmetic, rounded at the same point, in the same order. The two edits only change how fast duplicates are found and how often the regions file is read.

**How I checked:** I made a test file ten times the size of last night's export, with some repeated order IDs mixed in. I ran the old and new versions on both that file and the real one and compared the outputs: they're identical. The unit tests also pass.

The comment in `layout.py` calls the table formatting the "slow part", but it isn't. It only handles about 40 region rows and 5 customer rows, so I left it alone.

The test files are in `scratch/` next to `fixture/` (`big.csv` is about 6 MB), and you can delete them.