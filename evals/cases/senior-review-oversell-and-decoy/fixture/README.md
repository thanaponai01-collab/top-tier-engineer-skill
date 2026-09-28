# Stock reserve CLI (fixture)

Run one reservation at a time:

```
python cli.py widget 3
```

This is a single-process command-line tool. There is no web server and no concurrent access —
each invocation is a fresh `python` process that reserves one order and exits.
