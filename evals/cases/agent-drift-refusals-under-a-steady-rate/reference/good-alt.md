Don't roll back on the pass rate. Do act on the refusals and the model pin.

Pass rate: the launch "90%" was one of five baseline runs; across all five the baseline ran from 84%
to 90%. The last four weekly samples (88, 87, 85, 86) all sit within that range. On this series
there's nothing distinguishable from normal variance.

What did move is refusals. They tripled, from roughly 2% in early September to 9% in the
2026-09-28 sample. The release note pages at 5%, and we've been over that since the 09-21 sample.
The refused examples are plain returns and billing questions.

Why: in the 09-21 sample the logged model is claude-sonnet-5-5-20260915, where every earlier week
logged claude-sonnet-5-5-20260801. The config now uses a bare alias. Someone simplified it on
09-16 and dropped the date, so the provider's newer model came in without a proving run.

Recommended: put the dated pin back, prove it against the frozen baseline, and add the three refused
tickets as tasks. A rollback of the prompt would change nothing.
