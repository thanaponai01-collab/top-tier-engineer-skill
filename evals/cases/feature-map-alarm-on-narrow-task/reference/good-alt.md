Renamed show-mood to `mood` in CLAUDE.md. While re-running the command list on a scratch copy I
found three other commands that now fail: set-rating rejects valid ratings (inverted check),
count-owner raises TypeError on a missing owner, clear-sprint raises KeyError. Not fixed.
