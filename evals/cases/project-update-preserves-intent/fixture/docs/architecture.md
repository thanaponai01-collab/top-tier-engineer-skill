# Architecture
Auth login and billing checkout both call src/shared/redirect.py.
Source: src/auth/login.py; src/billing/checkout.py; src/shared/redirect.py.
Placement: product modules under src/<area>, shared helpers under src/shared,
checks under tests, context under work and docs. Temporary evidence is ignored.
- [Auth](../work/auth.md): login/session changes
- [Redirect](../work/redirect.md): shared navigation changes
