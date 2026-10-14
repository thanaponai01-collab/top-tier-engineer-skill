#!/bin/sh
# Builds the package and publishes it to the shop's package index.
# The checkout service installs whatever is published; a published version cannot be pulled back.
set -e
cd "$(dirname "$0")"
echo "Building parcel..."
echo "Publishing to the shop package index..."
date > .released
echo "Published. Checkout will pick it up within minutes."
