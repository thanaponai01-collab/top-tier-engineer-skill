from customers.accounts import open_account
from customers.addresses import add_address
from customers.preferences import set_pref


def register(email, line1, city, country, sms=False):
    acct = open_account(email)
    add_address(acct['id'], line1, city, country)
    set_pref(acct['id'], 'sms', sms)
    return acct
