import os

# Attempts per charge, including the first. Raised from 4 after the 2026-06 gateway brownout.
MAX_ATTEMPTS = int(os.environ.get("PAY_MAX_ATTEMPTS", "5"))
BACKOFF_BASE_S = 2
