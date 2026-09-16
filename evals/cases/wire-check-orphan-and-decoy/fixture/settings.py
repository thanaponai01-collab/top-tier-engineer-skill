# Job specs are resolved by scheduler.py with importlib; no import statement
# anywhere in this repo mentions the modules named here.
SCHEDULED_JOBS = ["handlers.digest:run"]
