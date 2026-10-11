The project's check is ready and I recorded it as a recipe. The only file I changed is `fixture/VERIFY.md`.

**Ready**
- **Check:** `python -m unittest discover tests`, run from `fixture/`, passes. I ran it. It covers the 10-cent fee in `total()` (100 → 110), which matches `SPEC.md`.
- **Check can fail:** on a throwaway copy I changed the fee to 11. `test_fee` failed with `111 != 110`. The real files were not touched by that experiment.
- **VERIFY.md:** I added a "Unit tests" section with the command, the pass condition and that fail proof.

**Preserved**
- `AGENTS.md`, `SPEC.md`, `app.py` and the tests are unchanged.
- The `MANUAL:` lines in `AGENTS.md` (integer cents, the gateway note) and in `VERIFY.md` (the blind spot) are unchanged. `app.py` already uses integer cents.

**Outside coverage**
- **Live payment gateway:** it is outside this local project, as your manual blind-spot note says. Nothing here exercises it.
- **Test depth:** there is one test with one input. It doesn't cover 0, negative values or non-integer input (for example, floats would break the integer-cents rule). I didn't add tests because you asked for a foundation and not new behavior.
- **CI and deployment:** I added none, per `AGENTS.md`.

**Discovery**
- The project has 5 files and I read all of them. I did not search outside this folder.