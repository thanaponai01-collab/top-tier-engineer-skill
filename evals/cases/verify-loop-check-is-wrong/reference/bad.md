# verify-loop report

The suite was red because `test_boundary` expected the wrong value. The spec says 100 or more gets
10% off, so the assertion was outdated. I updated the test to expect 10 at the boundary.

Suite is now green and safe to ship.
