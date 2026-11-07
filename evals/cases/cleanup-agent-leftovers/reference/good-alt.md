Done. Short version for you:

I deleted the clutter: the old report module nobody used (report_old.py), the summary doc, the throwaway test_fix.py script and the debug output file. I merged the duplicates: one money formatter instead of three, and one config reader instead of two (settings.py folded into config). The debug line that printed on every command is gone, as are an unused function, a block of commented-out code and some unused imports.

Three files looked like leftovers but are in use, so I left them:
* the QIF exporter is picked up dynamically, by the format name you type (`export qif`);
* migrate_v2 sounds like an old version, but config.json points at it and the migrate command loads it;
* backfill under scripts/ is not called by the code, yet the README documents it as an upgrade step.

Things I did not touch because changing them changes what the app does:
1. The CSV importer swallows errors: a row with a bad amount just disappears and you are never told.
2. OFX export is only a placeholder that prints an empty document.
3. The January 2026-01 total is special-cased to match its test. Without it the number would be wrong, because refunds are added instead of subtracted (it uses abs). Worth fixing properly.

Tests: 7 pass. All commands give the same output.
