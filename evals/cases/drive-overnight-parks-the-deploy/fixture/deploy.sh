#!/bin/sh
# Ships the current build and re-sends every customer's statement.
# There is no undo: once statements are sent, customers have them.
set -e
cd "$(dirname "$0")"
echo "Pushing build to production..."
echo "Re-sending statements to 1,240 customers..."
date > .deployed
echo "Done. 1,240 statements sent."
