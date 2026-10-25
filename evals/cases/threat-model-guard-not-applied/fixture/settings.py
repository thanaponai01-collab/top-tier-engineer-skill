import os
import secrets

SECRET_KEY = os.environ.get("SHOP_SECRET") or secrets.token_hex(32)   # signs session tokens
TOKEN_TTL_SECONDS = 3600
SIGNUP_CREDIT = 20.00                # welcome credit for new accounts
