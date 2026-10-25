Six things nothing reaches. The rest (every command, the admin tools, the scheduled jobs, the CSV/JSON/XML exporters
loaded by name, the low-bin alert) ran when I drove it.

1. bins_rebalance: the decorator is missing, so the registry never sees it. Register or remove.
2. _parse_legacy_asn in the inbound receive command: nothing calls it; only _parse_line is used. Remove.
3. Digest emails: the job builds the digest and throws it away; send_digest and the outbox never run. Fix the bug.
4. crossdock: behind CROSSDOCK_ENABLED = False. Ask ops.
5. on_bin_emptied listens for "bin.emptied" but the event sent is "bin.empty", a mismatch, so it never fires. Fix the name.
6. purge_audit: not listed in schedule.json, so it never runs. Schedule it.
