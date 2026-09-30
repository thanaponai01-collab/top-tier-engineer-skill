from core.ids import new_id
from core.util import clamp, as_cents, slug, first


ACCOUNTS = {}


def open_account(email):
    cid = new_id('cus')
    ACCOUNTS[cid] = {'id': cid, 'email': email.lower()}
    return ACCOUNTS[cid]


def get_account(cid):
    return ACCOUNTS.get(cid)
