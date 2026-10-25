import hashlib
import hmac
import time

import db
import settings


def _sign(payload):
    return hmac.new(settings.SECRET_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()


def make_token(user):
    payload = f"{user.id}:{int(time.time()) + settings.TOKEN_TTL_SECONDS}"
    return f"{payload}:{_sign(payload)}"


def current_user(headers):
    """The user a request's bearer token belongs to, or None."""
    token = headers.get("Authorization", "").removeprefix("Bearer ").strip()
    try:
        uid, expires, sig = token.split(":")
    except ValueError:
        return None
    if not hmac.compare_digest(sig, _sign(f"{uid}:{expires}")):
        return None
    if int(expires) < time.time():
        return None
    return db.user_by_id(int(uid))


def signup(username, password):
    if not username or not password:
        raise ValueError("username and password required")
    if username.lower() in db.USERS:
        raise ValueError("username taken")
    user = db.User(max(u.id for u in db.USERS.values()) + 1, username, password,
                   credit=settings.SIGNUP_CREDIT)
    db.USERS[username.lower()] = user
    return user


def login(username, password):
    user = db.USERS.get(username.lower())
    if user is None or not hmac.compare_digest(user.password, password):
        return None
    return make_token(user)
