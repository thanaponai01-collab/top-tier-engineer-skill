**Added rich, and found two old pins that came back.**

- **rich**: added `rich>=13.7` to requirements.in and recompiled; requirements.txt now pins
  rich 13.9.4 with markdown-it-py, mdurl and pygments under it. No code changed. Tests: 6 of 6 pass.
- **urllib3 is back on 1.24.1** (pulled in by requests). The last dependency check moved it to
  2.2.3; the lockfile now has the old version again, which has several published security
  advisories. Recompiling for rich would have kept it, so I moved it back to 2.2.3.
- **PyYAML is back on 5.3.1**, which has CVE-2020-14343 and also breaks requirements.in's
  `PyYAML>=6.0`. Moved it back to 6.0.2.

It looks like a merge took an old requirements.txt. Worth checking which branch did it.
