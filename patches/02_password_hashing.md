# Patch 02 — One-way password hashing (resolves F2)

**Cause:** `custom_encrypt`/`custom_decrypt` are symmetric; stored value is recoverable, key is in repo.
**Principle:** never be able to learn a user's password.

## Fix — bcrypt (already common in Flask stacks; add to requirements.txt)

`app/utils/auth.py` — add hashing helpers; keep `custom_encrypt` only for non-password tokens:
```python
import bcrypt

def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain: str, stored: str) -> bool:
    return bcrypt.checkpw(plain.encode('utf-8'), stored.encode('utf-8'))
```

`app/controller/user.py` — `createUser` stores `hash_password(data['password'])`.
`app/controller/admin.py` — same for `createAdmin`.

`app/views/auth.py` and `app/views/admin.py` — login compares by re-hashing:
```python
if user and verify_password(d['password'], user.password):
    ...
```
(Replaces every `custom_decrypt(string=user.password) == d['password']`.)

**Migration note (hands to data-evolution):** existing rows hold Fernet ciphertext, not bcrypt
hashes. Cannot rehash without the plaintext. Plan: on next successful login (where plaintext is
in hand), detect a non-bcrypt value, verify via the old `custom_decrypt` path once, then
overwrite with `hash_password`. Force-reset any account that never logs in within the cutover
window. This dual-read cutover is exactly a `data-evolution` expand/contract — see that skill.

**Also:** rotate `SECRET_KEY` out of source into an env var (see patch 05); the committed key is
now compromised regardless.

**Pre-verify:** create a user, read the DB cell — confirm it is a bcrypt `$2b$` string, not
recoverable. Log in with the right and wrong password — expect success then failure.
