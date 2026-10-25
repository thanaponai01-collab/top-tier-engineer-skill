I left a feature map in FEATURES.md. The short version:

Every command goes through notes.py, which looks the subcommand up in HANDLERS and calls the module
in commands/. Notes are read and written by store.py in notes.json.

- add, list, search and export all work. I ran each one; add and export were pointed at scratch copies.
- purge empties notes.json. I mapped it from the code but deliberately did not run it, because it
  would wipe the real notes. I only checked that it refuses without --yes.
- sync shows up in --help but does nothing useful: there is no handler registered for it, and running
  it raises a TypeError. I listed it under "not working" so nobody assumes it syncs.
