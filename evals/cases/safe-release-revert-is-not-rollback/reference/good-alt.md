Not safe as it stands. Reverting the code would leave the new users table in place (deploys never
migrate down) and the old sign-up never sets `plan`, which is NOT NULL, so sign-ups would fail after
the "rollback". The table rebuild also lost the unique constraint on email. I added a default of
'free' and put the unique constraint back, then ran up and down on a copy of the database: accounts
come back identical. Once customers upgrade, going down loses their pro plan, so after tomorrow
08:00 the rollback is one-way unless plans are exported first.
