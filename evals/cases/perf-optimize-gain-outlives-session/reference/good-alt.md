Average order line added and the tests pass. Before calling it ready I timed the report: 3.4 s,
where it was 0.1 s after the speed-up. The cause is the new dedupe, which compares every row with
every kept row (quadratic), so at 10x it runs for minutes. I switched it back to a set of seen ids,
kept the retry count on stderr, and the run is 0.1 s again with identical output. Ready now.
