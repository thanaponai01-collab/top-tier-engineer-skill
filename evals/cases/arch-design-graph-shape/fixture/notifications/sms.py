from notifications.templates import render
from customers.preferences import get_pref


SENT = []


def send(cid, template, ctx):
    if get_pref(cid, 'sms', False):
        SENT.append((cid, render(template, ctx)))
