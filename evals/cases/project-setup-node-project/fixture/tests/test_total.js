const assert = require('node:assert/strict');
const {total} = require('../app');
assert.equal(total(100), 110, 'expected total 110');
