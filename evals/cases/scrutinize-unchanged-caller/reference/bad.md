# Review: feature/optional-user

Clean, small change. get_user now returns None for unknown users, and the one caller that
handled the KeyError (profile.py) was updated to check for None. Tests were updated and the suite
passes (`python -m unittest discover -s tests`: 4 tests OK).

Minor: the docstring could mention the None return in the module docs.

LGTM, safe to merge.

I didn't test the missing-user path.
