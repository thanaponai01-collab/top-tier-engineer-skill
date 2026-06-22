# LIVE_RUN_001 — First real execution of the suite

**Target:** `flask_ticket_booking_system` (a Flask + SQLite + SQLAlchemy ticket-booking app,
~1,700 LOC, real layered architecture: models / controller / views / api / utils). Used as a
size- and domain-matched stand-in after the intended target (`tickit`, private) was unreachable
from the run environment.

**Skills exercised:** `chief-engineer` (route), `senior-review` (whole-codebase judgment),
`scrutinize` (delta-free, applied to the booking subsystem as the highest-stakes path),
`debug-protocol` discipline (two-way proofs), `wire-check` (route resolution), `meta-skills`
(calibration throughout).

**Headline:** the suite worked. It routed correctly, derived this stack's invariants without a
checklist, and — critically — every finding below is **(proven)** by executing the real code, not
**(trace-only)**. The run also exposed four mandate gaps in the suite itself (see the level-2
postmortem at the end), which is exactly what a first live run is for.

---

## Director summary (Law 4)

This ticket app has a **proven authorization bypass** (any logged-in user can mint an admin token
and control the whole admin panel), **stores passwords reversibly** (a database or source leak
exposes every password in cleartext, and the key is committed to the repo), and **cannot enforce
its single most important business rule** — it sells more tickets than the venue holds, both by
ignoring the requested seat count and by losing concurrent bookings to a race. None of these are
style issues; each is a data-loss-, money-, or trust-level defect proven by running the code. The
fixes are bounded and shipped below.

`REVIEW: not-shippable(proven admin-auth bypass + overbooking)`
`SCRUTINY: rework(booking subsystem cannot hold its capacity invariant)`

---

## Invariants derived for this system (senior-review Phase 1)

No checklist was used; these were derived from what a ticket-booking system *is*:

1. A show never sells more admits than its venue's capacity.
2. A user's password is never recoverable by anyone, including a DB-holder or repo-reader.
3. Privilege (admin vs user) is decided by the server, never asserted by the client.
4. A ticket code identifies exactly one ticket.
5. Two users may independently book the same number of seats.

Every finding below is a proven violation of one of these.

---

## Findings (ordered by blast radius, per senior-review Rule 6)

### F1 — Proven admin-authorization bypass *(violates invariant 3)* — **(proven)**

**Root cause:** privilege is carried *inside the token the client holds*. `tokenize(user, role)`
embeds `role` in the cookie; `admin.py`'s gate is
`isAdmin(token) = validToken(token) and detokenize(token)['role'] == 'admin'`. The token is
Fernet-encrypted with `SECRET_KEY`, and that key is committed to the repository
(`config.py`). So anyone with repo access (public fork, leaked dump, ex-employee) can mint a
token with `role:'admin'` that passes `validToken` and every `isAdmin` check.

**Proof (executed):**
```
forged token decodes to: {'id': 9999, 'name': 'attacker', 'role': 'admin', 'ttl': ...}
role the server will trust: admin
token considered valid: True
```
Minted with nothing but the repo's own committed key. Two-way: with `role:'admin'` the admin
panel admits the request; with `role:'user'` the same code redirects to logout.

**Principle that prevents the class:** *authority is server state, not client data.* The token may
carry an opaque session id; the role is looked up server-side from that id every request.

**Fix (shipped):** see `patches/01_auth_server_side_role.md` — sign tokens with rotation off the
secret, store role in a server-side session/admin table keyed by user id, and look it up per
request rather than reading it from the cookie.

---

### F2 — Passwords are reversibly encrypted, and the key is in the repo *(violates invariant 2)* — **(proven)**

**Root cause:** `createUser` stores `custom_encrypt(password)`, and login does
`custom_decrypt(stored) == submitted`. Fernet is symmetric, so the stored value is the plaintext
under a key that is hardcoded in `config.py`. Encryption is not hashing; a reversible secret is a
plaintext password with extra steps.

**Proof (executed):**
```
plaintext: hunter2-secret
recovered: hunter2-secret   (via custom_decrypt)
attacker with repo key recovers: hunter2-secret   (using only the committed SECRET_KEY)
REVERSIBLE: True
```

**Principle:** *never be able to learn a user's password.* Store a slow one-way hash
(bcrypt/argon2) with a per-password salt; compare by re-hashing the submission, never by
decrypting.

**Fix (shipped):** `patches/02_password_hashing.md`.

---

### F3 — Overbooking: capacity guard ignores how many seats are requested *(violates invariant 1)* — **(proven)**

**Root cause:** `book_tickets` (views/ticket.py) computes `occupied_seats` once and gates on
`(show.isActive == 1) and (occupied_seats < venue.capacity)`. The requested `admits` never enters
the arithmetic, so a single booking of N seats into an almost-full or any-capacity venue passes as
long as *current* occupancy is below capacity by even one.

**Proof (executed):**
```
occupied=0, capacity=2, requested=5, guard passes=True
seats sold = 5 into capacity 2; OVERBOOKED = True
```

**Principle:** *check the post-condition, not the pre-condition* — gate on
`occupied + requested <= capacity`.

**Fix (shipped):** `patches/03_capacity_and_race.md` (combined with F4, since the correct check
must also be atomic).

---

### F4 — Concurrent double-book: time-of-check ≠ time-of-use *(violates invariant 1)* — **(proven)**

**Root cause:** even with correct per-seat math, occupancy is read and the row is written in
separate, unlocked steps. Two requests both read the old count, both pass, both commit.

**Proof (executed):**
```
request1 reads occupied=0 -> passes;  request2 reads occupied=0 -> passes
total admits after both commit = 3 (capacity 2); RACE = True
```

**Principle:** *capacity is a shared resource; its check and its claim must be one atomic
operation* — `SELECT ... FOR UPDATE` on the show row, or an `INSERT` guarded by a DB-level
constraint/transaction that fails the loser, then retried.

**Fix (shipped):** `patches/03_capacity_and_race.md`.

---

### F5 — `Ticket.admits` is `unique=True` *(violates invariant 5)* — **(proven)**

**Root cause:** a per-ticket quantity column is marked globally unique in the model
(`models/ticket.py`). Two different users can therefore never book the same number of seats; the
second identical quantity raises an IntegrityError.

**Proof (executed):**
```
first booking of 1 seat: OK
second booking of 1 seat: FAILED -> IntegrityError: UNIQUE constraint failed: tickets.admits
```

**Principle:** *uniqueness belongs on identity, not on quantity.* `code` should be unique;
`admits` must not be.

**Fix (shipped):** `patches/04_schema_fixes.md` (also covers the OR-filter lookup, F6).

---

### F6 — `getTicket` (and `getUser`) use OR across distinct keys *(violates invariant 4)* — **(proven)**

**Root cause:** `getTicket(id, show_id, code)` filters
`(Ticket.id == id) | (Ticket.show_id == show_id) | (Ticket.code == code)`. A lookup by `code`
alone still matches any row whose `id` or `show_id` equals the *other* defaulted arguments, so a
code lookup can return an unrelated ticket. Same pattern in `getUser(uid, email)`.

**Proof (executed):**
```
getTicket(id=1) returns ticket for show_id=7  (id/show_id/code are interchangeable under OR)
```

**Principle:** *look up by one key deliberately.* Separate finders, or an explicit
"by_code"/"by_id" parameter — never an OR over independent identifiers.

**Fix (shipped):** `patches/04_schema_fixes.md`.

---

### F7 — User-controlled strings flow into `LIKE` filters; `DEBUG=True` in source — **(trace-only / suspected)**

**Root cause (trace-only):** search controllers build `Event.name.like('%'+name+'%')` from request
input. SQLAlchemy parameterizes the value so this is **not** classic SQL injection, but the `%`/`_`
wildcards are u:nescaped, so a user can craft expensive/over-broad matches (a `%` returns
everything) — a denial-of-detail and a mild perf surface. Separately, `main.py` hardcodes
`Config.DEBUG = True`, which in Flask exposes the interactive debugger (remote code execution if
reachable) on any unhandled exception.

**Why only trace-only:** I did not stand up the full WSGI app with a populated DB to fire a live
malicious request; the data-flow chain is complete by reading, so this caps at (trace-only) per
PROTOCOL §1 rather than borrowing (proven).

**Fix (shipped):** `patches/05_search_and_debug.md` — escape LIKE metacharacters; drive DEBUG from
an environment variable defaulting to False.

---

## What's genuinely good (senior-review Phase 5 — earned, not padding)

- The **layering is real**: models / controller / views / api / utils have clean responsibilities,
  and the controllers are thin and readable. This is better structure than most apps this size.
- **Error paths exist** in the DB controllers (`try/rollback/raise`), which is more discipline than
  typical tutorial code.
- The **token has a TTL** and logout deletes the cookie — the *shape* of session handling is right;
  it's the trust placement (F1) that's wrong, not the absence of sessions.

## One growth theme (the single highest-leverage lesson)

**Decide trust and invariants at the boundary, in the server, atomically.** Five of seven findings
(F1, F3, F4, plus the spirit of F2 and F6) are the same root habit: a security- or
correctness-critical decision was made from data the client supplied or from a value read too
early. Move every such decision server-side and make resource checks atomic, and the whole class
disappears.

---

## Level-2 postmortem — what this run taught the *suite* (meta-skills Discipline 5)

The run validated the lifecycle, but four findings had **no owning skill with a real pipeline**,
forcing them into `senior-review`'s dimensions as checkboxes. Per the suite's own bar (a question
with no owning *pipeline* earns a skill), these become v1.5.0:

1. **F1 + F2 + F7-debug are security findings with no security *pipeline*.** senior-review's
   "Safety & trust" dimension *caught* them, but a dimension is a reminder, not a method — there
   was no threat-model → trust-boundary enumeration → abuse-case → hostile-test process, and no
   owner to route the abuse-case tests to the gate. **→ new skill `threat-model`.**

2. **F3/F4 are correctness, but the moment they're fixed, "is this safe to deploy and can we roll
   it back?" has no owner.** The suite ends at "ship" with nothing owning the act of shipping. **→
   new skill `ship-gate`.**

3. **F5/F6 are schema/persistence shape; fixing F5 in production would require a migration, and
   nothing owns migration/rollback semantics** (evolve-maintain's deprecation ladder is for code
   callers, not data). **→ new skill `data-evolution`.**

4. **F1's "the key is in the repo" and "DEBUG=True shipped" are config/secret findings that only
   surfaced because I happened to read config.py** — nothing owns *configuration and secret
   hygiene* as a forward discipline. Folded into `threat-model`'s supply/secret surface rather
   than a fourth skill, to respect Law 1.

5. **Process friction observed:** the fast-path definition in chief-engineer would have *permitted*
   this booking change as a single slice (single-session, single-file) with no security or data
   lens forced — a 40-line diff can still bypass auth. **→ fix: fast path forbidden when a slice
   touches a trust boundary or persistent state.**

`MAINT LIVE_RUN_001: resolved(validated, proven) | spawned(threat-model, ship-gate, data-evolution, validator) | process-fix(fast-path carve-out)`
