Filed: **0**. The repo has no git remote and `gh` isn't authenticated (`gh auth status`: not logged in),
so nothing could reach a tracker. Bodies are built in `issues/` and nothing is filed. The audit stays
the queue until someone runs the commands below.

| item | issue | state | why |
|---|---|---|---|
| M1 one rounding rule | none | built, not filed | no remote |
| M2 tax per line | none | built, not filed | no remote; body says "Blocked by M1" |
| M3 clean up helpers | none | **held** | no proof line, and "tidy up" isn't a change anyone can finish |
| M4 tax breakdown on PDF | none | built, not filed | no remote; blocked by M2 |

Every body opens with the shared context: behind `TAX_V2` (off by default), auth model unchanged,
source: the 2026-10-06 tax review. Each body keeps what/why/where (with lines)/proof/order verbatim
from AUDIT.md.

To file once a remote exists, in order:
`gh issue create --title "M1: one rounding rule" --body-file issues/M1.md --label tax-audit`, then M2,
then M4, then stamp the numbers back into AUDIT.md.
