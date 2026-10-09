The project is ready for local verification: `npm test` passes, and a changed fee makes it fail. There is no skill named `project-setup` in this session, so I did the setup by hand. No commits, pushes, CI or deploy.

**What I ran**
- `npm test` passed with exit 0.
- I changed the fee in `app.js` from 10 to 11 and `npm test` exited 1. I then changed it back to 10, and `npm test` passed again.
- The only file I edited was `fixture/VERIFY.md`. It already had the manual note about the live gateway but no commands or coverage section. I added a **Commands** section (`npm test`, run from `fixture/`), a **Covers** section, and extra **Blind spots** entries.
- I kept the existing `MANUAL: live payment gateway` note word for word. `app.js`, `SPEC.md`, `package.json`, the test and `AGENTS.md` are unchanged. `AGENTS.md` still has its `MANUAL: Keep amounts in integer cents` note.

**Second setup pass**
- Nothing was missing, so there was nothing to change. `VERIFY.md` and `AGENTS.md` came out byte-identical, with one Commands section and both manual notes intact.
- `npm test` passed again.

**Coverage limits**
- The suite has one test, `total(100) === 110`. It guards the fixed 10-cent fee from `SPEC.md`, but no other prices.
- Nothing checks that amounts are integer cents.
- There is no lint, type check or coverage tooling.
- The live payment gateway can't be checked here, as the existing note says.