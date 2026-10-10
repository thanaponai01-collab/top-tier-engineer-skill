# Launch review

The proving round passed at 94% with all safety tasks green, so the agent itself is in good shape.

Controls:
- There's a kill switch (`enabled` in config.yaml) documented in LAUNCH.md.
- Cost is capped at $0.40 per conversation.
- Runs are logged to logs/runs.jsonl so we can review them.
- There's no step cap, so a confused run could loop forever. Add a max_steps limit.

Recommendation: add a step cap, then launch Monday as planned.
