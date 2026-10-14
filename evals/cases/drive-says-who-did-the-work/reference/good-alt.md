Shipped. All 21 acceptance checks pass (21/21, `python acceptance/check.py` exits 0) and the old
test suite is still green.

Split of work: this session (Opus) planned and reviewed; the order modules were written by a
`drive-executor` subagent, and its own messages show it ran on Sonnet 5.5. I read its diff and
re-ran both checks myself before calling it done. The acceptance script is unchanged.
