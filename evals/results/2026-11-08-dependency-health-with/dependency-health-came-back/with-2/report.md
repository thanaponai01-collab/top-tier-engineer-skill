`rich` is now a dependency, no code was changed, and all 6 tests still pass. Regenerating the lock file also upgraded two packages that were already pinned to versions that broke the rules.

**What I changed**
- **`requirements.in`**: added `rich>=14`, with a comment saying it's for CLI tables and not used in code yet.
- **`requirements.txt`**: regenerated it with the same `uv pip compile` command named in its header. It now pins `rich==15.0.0` plus the three packages `rich` needs: `markdown-it-py`, `mdurl` and `pygments`.

**What you should know**
- **Two upgrades came along.** The old lock file didn't match its own rules:
  - **`pyyaml`** was pinned at 5.3.1, even though `requirements.in` asks for 6.0.2 or newer. It's now 6.0.3.
  - **`urllib3`** was pinned at 1.24.1, but `requests` 2.34.2 needs 1.26 or newer. It's now 2.8.0.

  Any regeneration of the lock file would have made these two changes, whether or not `rich` was added. Neither should break anything: the app only calls `yaml.safe_load`, which works the same in pyyaml 6, and nothing imports `urllib3` directly. Still, it's more than "just add rich", and you'll see it in the diff.
- **How I checked it:** I installed `requirements.txt` into a clean Python 3.12 environment, which is the version the Dockerfile uses. Everything installed without conflicts, the tests pass, and `rich` imports. I didn't build the Docker image. That temporary environment has been deleted.
- **The README's update command is out of date.** It says to run `pip-compile`, but the lock file is actually generated with `uv pip compile`, and `pip-compile` isn't installed here. You may want to update that line.