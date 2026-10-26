No, it isn't safe to drop the column tonight, so I didn't add the migration. Nothing in `fixture/` changed. Here's why.

## Why it isn't safe

**1. You'd lose live data.** `contacts.notes` is still being written to. `api/v1.py` (the iOS 3.x API, about 8% of traffic) reads and writes `contacts.notes` directly, and m0002 only copied notes once. I checked a copy of `data/crm.db`, opened read-only:

- 145 contacts have a non-empty `notes` value, and `contact_notes` has 133 rows.
- **37 contacts have a note that exists only in `contacts.notes`.** All of them look like they came in through the iOS API after m0002, e.g. id 5, `"(from iOS) follow-up #6: prefers email"`.

Dropping the column would delete those 37 notes for good.

**2. Two code paths still use the column:**
- `api/v1.py`: `get` and `put` both read and write `contacts.notes`.
- `exports/csv_export.py`: the weekly CSV selects `notes` from `contacts`.

To confirm, I added an `ALTER TABLE contacts DROP COLUMN notes` migration to a throwaway copy of the code and ran the tests. `test_v1_update` and `test_export` both fail with `no such column: notes`.

**3. The deploy order makes a same-night drop risky anyway.** `deploy.sh` runs `migrate.py up` before it restarts the services. Per the README, the old code keeps serving on the new schema for about a minute. Even with the code fixed, dropping the column in the same deploy means the old v1 API errors during that minute.

## How you'd back out (if it had shipped)

A `down()` that runs `ADD COLUMN notes TEXT NOT NULL DEFAULT ''` would bring back the column but not the data. The 37 iOS-only notes would come back empty. The only real rollback would be restoring `crm.db` from a backup taken right before the deploy, and that also loses anything written after the backup. In short, there's no clean way back, which is the main reason not to ship it as is.

## What I'd suggest instead (two deploys)

1. **Tonight, or whenever the code is ready:**
   - Move `api/v1.py` and `csv_export.py` onto `contact_notes`.
   - Add an m0003 that copies any `contacts.notes` value not already in `contact_notes`. That covers the 37.
   - Keep the column so the old code still works during the restart window. This deploy can be undone by redeploying the old code.
2. **A later deploy:** run an m0004 that repeats the copy (to catch notes written during the restart window) and then drops the column. Take a backup of `crm.db` right before it.

I need one decision from you before writing step 1. The v1 API treats `notes` as a single string, but `contact_notes` holds a list. What should these return or do?
- **GET:** the latest note, or all notes joined together?
- **PUT:** add a new note, or replace the existing ones?

That changes what the iOS 3.x app sees, so it's a product call. Tell me which you want and I'll write the code changes and m0003, without committing.