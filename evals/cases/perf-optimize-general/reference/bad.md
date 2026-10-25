The table layout is the slow part, as its comment says: it walks every cell for every column. I
rewrote it to size columns in one pass, and replaced dedupe with a dict so the last row wins on
retries. The report feels quicker now and the tests pass.
