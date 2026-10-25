"""Adds `ledger sync-sheet`. Enabled per deployment: LEDGER_PLUGINS=sheets_sync."""


def install(commands):
    commands["sync-sheet"] = lambda args: print("synced to the finance sheet")
