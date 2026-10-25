Answers (checked in a scratch copy, your pantry.json untouched):

1. The "Use 1" button in each row (data-testid="use-btn"); it POSTs to /api/items/{id}/use.
2. Run `pantry.py shop`. Anything whose quantity is less than its minimum is listed.
3. Two: "/" jumps to search, and Ctrl + Enter adds the item in the form.
4. Not today: import crashes with KeyError 'quantity' on a file export wrote (export's column is qty).
5. It doesn't work: /api/stats raises KeyError: 'qty', because usage entries are saved with "n".
6. There is no scan command; `pantry.py scan` gives "invalid choice". The README describes something not built.
7. /debug/dump, only with PANTRY_DEBUG=1 in the server's environment. Normal users get a 404.
8. use_item in store.py.
9. Everything: `wipe --yes` clears all items and the used log. It refuses without --yes.
