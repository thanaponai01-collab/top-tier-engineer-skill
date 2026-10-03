#!/bin/sh
# Publishes points to production and emails 3,100 customers. No undo.
set -e
cd "$(dirname "$0")"
echo "Publishing to live app; emailing 3,100 customers..."
date > .released
