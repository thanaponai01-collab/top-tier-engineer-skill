from customers.accounts import get_account


def current_account(token):
    return get_account(token.split(':')[0])
