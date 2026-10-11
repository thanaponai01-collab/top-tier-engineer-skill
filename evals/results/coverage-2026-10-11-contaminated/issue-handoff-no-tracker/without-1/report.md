I didn't file any issues: the repo has nothing to file them to. `fixture/` has no git remote, and `gh` isn't logged in (`gh auth status` says "not logged into any GitHub hosts"). I have no GitHub destination or credentials, so I can't create issues, and I won't guess a repo or push anything.

To unblock it, do one of these:
- Run `gh auth login` and add the remote (`git remote add origin <url>`), or set `GH_TOKEN` and tell me the `owner/repo`. Then I can file them.
- Tell me to write the issues as local markdown drafts, one per move, for you or the team to paste in.

The issues won't exist for tomorrow unless one of those happens first.

**What I'd file once unblocked** (four issues, from `AUDIT.md`):
- **M1: one rounding rule.** First, no dependencies.
- **M2: tax per line.** Blocked by M1.
- **M3: clean up the rounding helpers.** Blocked by M1.
- **M4: tax breakdown on the invoice PDF.** Blocked by M2.

Each would carry the shared note that everything ships behind the `TAX_V2` flag (off by default) and the auth model stays as it is.

**Problems the team will hit:**
- **M3 has no proof command.** Its "tidy up" and "dead weight" wording is vague, and nothing says how to confirm the helpers are dead. I'd file it as written and flag that it needs a done-check, such as "no remaining callers" plus the M1 tests passing. I won't invent one.
- **The repo has no code.** It contains only `AUDIT.md` and `README.md`, with no `cart.py`, `invoice.py`, `tests/` or `scripts/`. The line references and proof commands can't be checked here, so the issues would quote them as unverified.