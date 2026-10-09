# Recall capsule

GOAL: Help accounting export invoices as parseable JSON grouped per tenant, with invoice_id and amount and no cross-tenant mixing. [BRIEF.md]

DECISIONS: JSON replaces CSV; retain source identifiers for auditing in all areas 0–34. [BRIEF.md; brief/auditing-0-19.md; brief/auditing-20-34.md]

DONE: Re-ran `python -B check.py`: “CSV check passed”; `git diff --exit-code 8e5b17c -- exporter.py check.py` passed. These prove only the one-invoice CSV baseline, not JSON. [proven: check.py; exporter.py; Git]

IN FLIGHT: On master at the sole commit 8e5b17c; product files match it. AGENTS.md, BRIEF.md, BUILD.md, both archives, brief/ and __pycache__/ are untracked; no tracked product diff. [traced: Git status/log/diff]

OPEN: Exact JSON envelope, empty-input shape and invalid/missing-field validation remain assumptions requiring agreement. Live email delivery is deferred for missing credentials. [BRIEF.md assumptions/open questions; BUILD.md deferred]

BROKEN: Current export uses csv.DictWriter and returns CSV. Existing check only asserts its header, leaving current JSON acceptance and error paths unverified. [traced: exporter.py → check.py; BRIEF.md acceptance]

NEXT: Define and run a requirement-backed check for parseable JSON containing distinct t1/t2 groups, invoice_id and amount, and preserved source identifiers; retain the baseline rejection before implementing. Completion of this next step is a meaningful failing JSON check, not another green CSV replay. JSON proof must precede monthly wiring. [BUILD.md Next; BRIEF.md; linked auditing requirements]

NOT READ: Retired BRIEF.archive.md, detailed historical BUILD.archive.md receipts, and bytecode; current notes say the 200 receipts repeat one CSV check and do not prove JSON. No provider contacted or implementation changed. RUN.json, VERIFY.md, FEATURES.md and WHY.md are absent from the workspace inventory. [AGENTS.md; BUILD.md; rg --files]

UPKEEP: `context_budget.py` reports 7 context files, 0 over budget. Start-here block exists. [proven: recall context-budget command; AGENTS.md]
