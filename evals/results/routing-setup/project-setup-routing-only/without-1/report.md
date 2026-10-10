I added a short coordination policy to `fixture/CLAUDE.md` and left the owner note untouched.

- **Owner note:** "Amounts must preserve cents." is unchanged and still sits at the top of the file.
- **Added:** a `# Agent coordination policy` section with eight bullets. They cover reading before changing, verifying from the session, minimal edits, asking before irreversible actions, stopping after two failed attempts, and plain reporting. It also has a money rule to keep cents accurate.
- **Not touched:** `app.py`. I read it, and `total()` returns the float literal `42.35`. That fits the cents rule, but I haven't checked any arithmetic path, so I left it alone.

I read both files and made one edit; I didn't run anything. The directory isn't a git repository, so there's no commit or diff to show.