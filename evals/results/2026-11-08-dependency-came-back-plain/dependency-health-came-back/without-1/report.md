I added `rich` as a dependency without touching any code, and the 6 tests pass. Regenerating the lock file also upgraded two packages that were pinned to old versions, and the `render` command crashes for a reason unrelated to this change.

**What I changed (only these two files):**
- **`requirements.in`**: added the line `rich>=13`.
- **`requirements.txt`**: regenerated with `pip-compile --strip-extras requirements.in`, the command named in the file's header and the README. It now pins `rich==15.0.0` plus the three packages rich needs: `markdown-it-py`, `mdurl` and `pygments`.

**Two other version changes you should know about.** Regenerating moved two pins:
- **PyYAML 5.3.1 → 6.0.3.** The old lock file had drifted out of step with `requirements.in`, which asks for `PyYAML>=6.0`, so 5.3.1 broke your own rule. Regenerating had to fix it. The upgrade is safe for your code because `loader.py` uses `yaml.safe_load`, which works the same in 6.x.
- **urllib3 1.24.1 → 2.8.0.** This is what `requests` uses underneath. 1.24.1 dates from 2018 and has known security fixes missing, so the upgrade is a good thing, but it is a major version jump.

All other pins stayed the same.

**How I checked it:** I installed the new `requirements.txt` into a fresh environment, and `pip check` found no conflicts. The tests (`python -m unittest discover tests`) ran 6 and all passed. I deleted the temporary environments afterwards.

**The `render` crash:** `python -m tripbook render trips/bangkok.yaml` stops with `'dict object' has no attribute 'depart_dt'`. The template `templates/itinerary.html` uses `leg.depart_dt`, but no code ever sets it, so the command fails whatever package versions are installed. I left it alone because you asked for no code changes. The tests don't cover rendering, which is why they still pass. I can fix it if you'd like.