# Agent release: order assistant, Monday launch

**Verdict: blocked.** It can't be switched off without a deploy, the version that passed proving
isn't pinned, the logs can't be safely stored or replayed, and it goes to every customer at once.

| # | control | state | evidence |
|---|---|---|---|
| 1 | Kill switch | **missing**: `enabled:` is read once at process start (`assistant/settings.py`); `LAUNCH.md` says off = edit + redeploy, about 25 minutes | traced |
| 2 | Caps | steps: **present** (`max_steps: 12`, enforced in `loop.py`, stops and logs); per-run cost: present ($0.40); **no daily cap** (~3,000 × $0.40 ≈ $1,200/day, nothing stops a runaway) | traced |
| 3 | Pinned versions | **missing**: `model: sonnet` is an alias; `prompt: latest` picks the newest file in `prompts/`, so a new prompt file ships the moment it lands | traced |
| 4 | Logged runs | **unsafe**: `runlog.py` writes `customer_email`, `customer_address` and full message text unredacted; no model/prompt version, no cost per run, so a run can't be replayed against what produced it | traced |
| 5 | Staged rollout | **missing**: "turn it on for all customers"; refunds ≤ $200 go out without a human from minute one | traced |

Smallest fixes before Monday:
1. Read `enabled` per request from a flag service or a file re-read on each run, so off = one command, no deploy.
2. Pin `model:` to a dated id and `prompt:` to a file name. Changing either re-runs the proving round.
3. Redact email/address before writing. Add `model`, `prompt` and `cost` to every log line.
4. Shadow mode first (draft replies, no tool side effects), then 5% of chat traffic. Name the pass rate
   you'll compare against and who watches it. Refunds stay human-approved until the slice is clean.
5. Add a daily spend cap at the provider and in the loop.

The step cap is fine as it is. Not run: nothing executed, all of this is from reading the code.
