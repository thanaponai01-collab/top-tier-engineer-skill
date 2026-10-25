# Benchmark validity

Timing counts only when the intended work succeeds. Before measuring or accepting saved results:

1. **Pin the workload and decision.** Record input/version, expected output, useful work unit,
   user journey boundaries and the owner's target. Label missing conditions and assumed targets;
   do not silently invent an adoption threshold.
2. **Count real work.** For each run retain attempted and successfully completed useful units,
   errors and an independent output check (expected checksum, reference or invariant). Zero work,
   dropped requests, wrong output and error-heavy speedups fail validity. Report failures alongside
   timing; do not hide them by filtering successes. Compare equal useful work, or explicitly report
   throughput per successful unit and the different workload. Unknown counts/correctness prevent adoption.
3. **Compare fairly.** Record artifact, build mode/compiler flags, hardware, dependency versions,
   cache state, concurrency and resource limits. Debug versus release cannot establish a code gain.
   Re-run with comparable configurations; do not compensate using an assumed multiplier.
4. **Alternate comparable runs.** Interleave baseline/candidate, controlling warm-up and cache
   policy, to expose drift. Retain samples, order, median and variation; user journey measurements
   accompany micro timings. Choose sampling effort from observed variability and a stated time/cost
   budget, not an arbitrary minimum iteration count. Do not claim reliable tails from sparse samples.
5. **Name the limiter.** Record the constrained resource and evidence: CPU, I/O, network, lock,
   rate cap or another measured boundary. Unknown stays unknown. Profile separately from timed runs;
   profiler overhead must not decide the gain.
6. **Decide honestly.** Correct and comparable comes before faster. If the apparent gain is within
   noise, order/configuration is confounded, or the journey gain is unmeasured, label it inconclusive
   and name the bounded next experiment. Never retry until green or turn micro gains into user gains.

Report: workload/configuration | attempted/completed/errors/output check | samples/order |
micro median/spread | journey median/spread | limiter | valid, rejected or inconclusive and why.
Saved data supports analysis only; without a runtime, propose the experiment without claiming it ran.
