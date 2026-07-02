# Patch 01 — Server-side role (resolves F1: admin-auth bypass)

**Cause:** role lives in the client-held token; `isAdmin` trusts `detokenize(token)['role']`.
**Principle:** authority is server state, not client data.

## Minimal fix (keeps the existing token mechanism, removes the trust placement)

`app/models/admin.py` — admins are already a separate table; make membership the source of truth.
Stop writing `role` into the token; derive it server-side from the admin table on every request.

`app/utils/auth.py` — drop `role` from the token payload:
```python
def tokenize(user):
    d = {'id': user.uid, 'name': user.name,
         'ttl': (time.time_ns() + (86400000000000*2))}
    return custom_encrypt(string=json.dumps(d)).decode('utf-8')
```

`app/views/__init__.py` — `authorizeUser` no longer takes/sets a role.

`app/views/admin.py` — `isAdmin` looks up membership instead of reading a claim:
```python
from ..controller import getAdmin   # already imported nearby

def isAdmin(token):
    if not validToken(token):
        return False
    uid = detokenize(token)['id']
    return getAdmin(uid=uid) is not None   # server decides, every request
```
(Ensure `getAdmin` accepts a `uid=` lookup; add it if it only takes `email=`.)

**Out of scope:** replacing Fernet-token sessions with a signed/opaque-session library. That is the
*correct* long-term move (a token should carry an opaque id, not a JSON identity), but it is an
arch-design decision (one-way door on session format) — escalate via `arch-design`, do not smuggle
it into this fix.

**Pre-verify (the check ship-gate/correctness-gate runs):** mint a `role`-free user token, hit
`/admin` — expect redirect to logout. Add an admin row for that uid, hit `/admin` — expect 200.
Attempt the old forge (inject `role:'admin'` into payload): now inert, because role is never read.
