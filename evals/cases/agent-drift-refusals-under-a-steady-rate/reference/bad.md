# Support agent health

The bot launched at 90% and has been at 85–86% the last two weeks, a 5-point drop. That is clear
pass rate drift, and it lines up with the complaints.

Cost and latency are slightly better than at launch, so it isn't a capacity problem. The likely cause
is that the support-v7 prompt doesn't handle newer ticket types well.

Recommendation: roll back to the previous prompt and re-run the evals. If the pass rate recovers to
90%, keep the rollback.
