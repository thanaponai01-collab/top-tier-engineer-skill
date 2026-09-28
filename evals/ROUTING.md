# Routing — does the agent pick the right skill by itself?

Each row is a request someone might really type, naming no skill. The agent had this plugin
loaded and was left to choose. **Right** means the first skill it opened is one that fits;
for the last few rows, the right answer is that no skill of this plugin loads at all.

- **When:** 2026-09-27-0701
- **Model:** claude-opus-5-5
- **Agent's own pick:** 17 of 32 right
- **The plugin's hint** (the `route-hint` hook, which fires before the agent thinks): 14 of 32 right
- **Cost of this run:** $4.92

| Request | Should open | Hook hinted | Agent opened | |
|---|---|---|---|---|
| The nightly digest stopped going out after yesterday's deploy and I have no idea why. | `debug-protocol`, `drive` | `safe-release` ✗ | nothing | **wrong** |
| The export sometimes returns the wrong totals. Figure out what's going on. | `debug-protocol`, `drive` | — | nothing | **wrong** |
| Change scheduler.py to import the digest job directly instead of loading it by name from settings. Don't break the nightly run. | `evolve-maintain`, `build-discipline`, `drive` | — | nothing | **wrong** |
| I want to turn this into an app where my team can log which customers they called this week. Where do we start? | `problem-framing`, `drive` | — | nothing | **wrong** |
| We need a real job queue for the digest instead of cron. How should this be structured: Postgres queue or Redis? | `arch-design` | — | nothing | **wrong** |
| Draw me a picture of how the pieces of this service connect. | `arch-map` | `arch-map` | `top-tier-engineer:arch-map` | right |
| I wrote the export handler but hitting it does nothing. Is it even hooked up? | `wire-check` | `wire-check` | nothing | **wrong** |
| Before this goes out: does the health check actually do what it should? Test it properly. | `correctness-gate` | — | nothing | **wrong** |
| The health check takes eight seconds to answer under load. Make it fast. | `perf-optimize` | — | nothing | **wrong** |
| We're about to expose the export endpoint to anonymous users on the internet. Can someone abuse it? | `threat-model` | `threat-model` | nothing | **wrong** |
| Be honest: is this codebase any good? What's the biggest problem? | `senior-review` | — | nothing | **wrong** |
| Can you give me a second opinion on this code before I merge it? | `scrutinize`, `senior-review` | `scrutinize` | `top-tier-engineer:scrutinize` | right |
| The handlers folder feels like spaghetti. Is it, or is it just me? | `structure-gate` | `structure-gate` | `top-tier-engineer:structure-gate` | right |
| What code in here is dead and safe to delete? | `latent-audit` | `latent-audit` | `top-tier-engineer:latent-audit` | right |
| Ship this to production tonight. | `safe-release` | — | nothing | **wrong** |
| I need to rename the email column to contact_email in the users table on the live database. | `safe-release`, `evolve-maintain` | — | `top-tier-engineer:safe-release` | right |
| Upgrade this service to the newest Python version without breaking anything. | `evolve-maintain`, `drive` | `evolve-maintain` | nothing | **wrong** |
| Get the export handler routed and working. Keep going on it overnight, I'm going to sleep. | `drive-overnight` | `drive-overnight` | `top-tier-engineer:drive-overnight` | right |
| Where were we? Catch me up on this project. | `recall` | `recall` | `top-tier-engineer:recall` | right |
| Why does the scheduler load digest by name from settings instead of importing it? Who decided that? | `code-history`, `explain` | `code-history` | `top-tier-engineer:code-history` | right |
| Walk me through how a request travels through this app. Don't change anything. | `explain`, `feature-map` | `explain` | `top-tier-engineer:explain` | right |
| What features does this app actually have, and how do I reach each one? | `feature-map` | — | `top-tier-engineer:feature-map` | right |
| Here's the plan: 1) route the export handler, 2) add a test for the digest, 3) add auth to export. File these as tracked issues. | `issue-handoff` | — | `top-tier-engineer:issue-handoff` | right |
| Set this repo up so the engineering skills work well in it. | `project-setup` | — | `top-tier-engineer:project-setup` | right |
| Add a header comment to export.py, and check your own work until it really passes. | `verify-loop`, `build-discipline` | — | nothing | **wrong** |
| I want to add an LLM agent that writes the nightly digest. How do I know if it's any good before I build it? | `agent-evals` | — | `top-tier-engineer:agent-evals` | right |
| Our support agent passes sometimes and fails other times. Does it actually work? | `agent-prove` | `correctness-gate` ✗ | nothing | **wrong** |
| My coding agent deleted handlers/health.py last night when I asked it to clean up imports. Why did it do that? | `agent-trace` | — | `top-tier-engineer:agent-trace` | right |
| We're about to put our AI agent in front of real customers. What do we need first? | `agent-release` | — | nothing | **wrong** |
| Fix the typo in health.py's docstring if there is one, otherwise add one that says 'Liveness probe.' | nothing of this plugin | — | nothing | right |
| What does HTTP status 418 mean? | nothing of this plugin | — | nothing | right |
| Rename the function check() in handlers/health.py to ping() and update its caller. | nothing of this plugin | — | nothing | right |

✗ marks a hint that points at the wrong skill. A hint that is wrong is worse than none: it
pushes the agent toward the wrong instructions.

A wrong row is either a description that doesn't say when to use the skill, or two skills
that overlap. Fix the description, or merge the skills, and re-run `python evals/route_live.py`.
