Found it: it's a misspelt hostname, not a slow page.

I timed `python dashboard.py` first: about 6 seconds. Nearly all of that is the feature-flag fetch.
settings.py, which was edited yesterday, has FLAGS_URL on flags.internal.exmaple instead of
flags.internal.example. That host never responds, so each of the 3 attempts waits the full 2-second
timeout, and then the page quietly renders with default flags.

I corrected the hostname. The dashboard now renders in a few milliseconds and gets the real flags
again (new navigation is back on). I didn't touch the widget ordering. It's a naive sort, but over
50 items it costs nothing measurable.
