# Structure Gate — fixture/

**In places.** The mess is concentrated in one function; the rest of the code is small and readable.

Measured: 201 code lines, 93% entered by the Python parser; the 14 lines of `static/app.js` got
length and duplication checks only (read by hand: two short functions, nothing to flag).

| signal | where | measured | what it costs the next person |
|---|---|---|---|
| complexity | `invoicing/pricing.py:compute_price` | 31 branch points, nested 6 deep, 64 lines | every discount rule lives here; a new discount type is one more branch among ~30, and the one test covers a single path, so a change can break VIP or shipping pricing without anything failing |
| import cycle | `invoicing/models.py` <-> `invoicing/store.py` | 2 modules import each other | neither can be loaded or tested alone; a reordered import can break startup |
| duplication | `export_csv.rows_for`, `export_json.records_for` | the same 6-line block twice | a change to how an invoice is normalised has to be made twice, and the two exports drift |

`cli.py`, `util`-sized modules and the exports' write functions are small and simple.

Before adding the discount type, pull the coupon rules out of `compute_price` into their own
function so the new one has a place that can be tested alone.
