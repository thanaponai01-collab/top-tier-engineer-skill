# Release check

The suite is green (`python -m unittest`, 2 tests OK) and `app/profile.py` already reads from the
new `contacts` table, so migration 003 lines up with the code. The migration is small and
straightforward.

Verdict: good to go. Follow `DEPLOY.md`: run the tests, `python migrate.py data/prod.db`, restart.
