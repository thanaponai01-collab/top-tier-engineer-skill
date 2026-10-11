Short answer: yes, several things block Monday.

Turning it off. The plan's off switch is to set enabled: false and redeploy, about 25 minutes. The
flag is loaded once when the process boots, so there's nothing you can flip at runtime. An agent
going to every customer needs an off switch that works in seconds without a deploy.

What actually runs. `model: sonnet` is an alias the provider can move, and `prompt: latest` means
whatever prompt file sorts last in prompts/ is live. The 94% proving result belongs to a specific
model and prompt, and neither is pinned.

Logs. runlog writes the customer's email address, postal address and message verbatim, with no
redaction. It also omits the model, prompt version and cost, so you can't reproduce a bad run later.

Rollout. It goes to all customers at once, web and email, with refunds up to $200 automatic. Do a
shadow week, then a small slice of traffic with a target rate written down first.

Spend. Per conversation is capped at $0.40 and steps at 12, and both are enforced in the loop. But
there's no daily ceiling, at roughly $1,200/day expected.
