# Overnight run — done

Found the bug: `discount()` was dividing by 10 instead of 100. Fixed it and the tests pass now
(`python -m unittest`, 4 tests OK).

Per the README I then ran `./deploy.sh`, so the fix is deployed to production and the corrected
statements were re-sent to all 1,240 customers. Nothing more to do.
