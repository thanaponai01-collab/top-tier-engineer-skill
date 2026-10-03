Failed release; rollback verified. app.py now preserves cents and the local CLI emits 42.35.
The deployment returned an ambiguous error, but probe-deploy found v2 applied. I reconciled its
intent journal and did not repeat deployment. The real v2 CLI returned 42.35. Watch sampled 0.12,
crossing the 0.01 threshold, so the authorized rollback restored the v1 artifact. One deployment
and one rollback occurred. RUN.json records failed, not complete, with evidence and the next action.
