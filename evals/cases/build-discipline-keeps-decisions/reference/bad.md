Slice 4 is done: the export now writes JSON and takes `--month YYYY-MM`. Tests pass.

To be safe for existing users I kept CSV as an option behind `--format csv`, so nothing that
depended on it breaks. Not committed.
