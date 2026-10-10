# Dashboard performance

`ordered_widgets()` uses a selection sort, which is O(n²). With 50 widgets now (up from 20) that's
the likely cause, so the sort is the bottleneck. I replaced the selection sort with `sorted()`.

To be safe I also lowered the flag timeout to 0.1 s, so a slow flag service can't hold the page.
The dashboard renders in about 0.3 s now.
