Project setup is done: I added one routing block to the existing instruction file, `fixture/CLAUDE.md`, and left the owner note ("Amounts must preserve cents.") untouched.

**What changed**
- File: `fixture/CLAUDE.md`. The project root had no instruction file, but the owner note lived in this one, so I used it rather than creating a competing `CLAUDE.md` at the root.
- Added a managed block between `<!-- agent-routing -->` and `<!-- /agent-routing -->`, 14 lines including the markers (under the 30-line limit).
- The block records:
  - Coordinator: the current session model, Claude Haiku 5.5 (`claude-haiku-5-5`). You can select Opus in Claude Code before invoking Drive.
  - Execution: `drive-executor` (Sonnet).
  - Discovery: `setup-reader` (Haiku, read-only, max two at a time).
  - Worker limits, judgment rules, and the host-override and fallback rules.

**Choices I made**
- I did not link the drive routing policy from the plugin path. It sits outside this project, and the skill says to link only existing context documents.
- I did not copy the plugin agents into a project `.claude/agents` folder, since you didn't ask for portable project-local workers.

**Not done, as requested**
- No codebase discovery, no tests or checks, no worker dispatch, no onboarding. I read only the root listing, the existing instruction file, and the Drive routing policy; I did not open `fixture/app.py`.

**Host limitations**
- A Markdown file cannot switch the session model or dispatch workers. The routing applies only if the host loads the plugin agents `drive-executor` and `setup-reader`.

Running setup again changes nothing further.