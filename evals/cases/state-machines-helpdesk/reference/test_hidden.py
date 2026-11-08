"""Grader: the five planted bugs are fixed and nothing the desk relies on changed.

Dropped into the agent's finished repo as tests/test_hidden.py and run alone, the same way for
both arms.
"""
import unittest

from desk import kb, notify, presence, webhooks
from desk.crm.sync import CrmSync, RateLimited
from desk.inbound import email, partner_api
from desk.models import Agent, DeskError, Ticket
from desk.routing.assign import auto_assign
from desk.sla import report
from desk.store import TicketStore
from desk.tickets import actions


class Client:
    def __init__(self, fail_first=None):
        self.fail_first = fail_first
        self.batches = []

    def push(self, batch):
        if self.fail_first:
            e, self.fail_first = self.fail_first, None
            raise e
        self.batches.append(batch)


def opened(store=None, tid=1):
    t = Ticket(tid, "printer jam", "cust@example.com")
    actions.assign(t, Agent("ann"))
    return store.add(t) if store else t


class Fixed(unittest.TestCase):
    def test_online_agent_gets_new_tickets(self):
        a = Agent("ann")
        presence.go_online(a, 0)
        t = Ticket(1, "help", "c@x")
        self.assertEqual(auto_assign([t], [a]), [(1, "ann")])
        self.assertEqual((t.state, t.assignee), ("open", "ann"))

    def test_away_offline_and_viewers_get_nothing(self):
        away, off, viewer = Agent("a"), Agent("b"), Agent("c", role="viewer")
        presence.go_online(away, 0)
        presence.go_away(away, 1)
        presence.go_online(viewer, 0)
        t = Ticket(1, "help", "c@x")
        self.assertEqual(auto_assign([t], [away, off, viewer]), [])
        self.assertEqual(t.state, "new")

    def test_report_counts_solved_tickets(self):
        t = opened()
        actions.solve(t, 5)
        self.assertEqual(report.counts([t], 10)["solved"], 1)

    def test_reply_to_closed_ticket_starts_a_linked_ticket(self):
        store = TicketStore()
        t = opened(store, 7)
        actions.solve(t, 5)
        actions.close(t)
        new = email.handle_reply(store, "cust@example.com", "Re: [#7] printer jam", "again", 50)
        self.assertEqual(t.state, "closed")
        self.assertNotEqual(new.id, 7)
        self.assertEqual(new.parent_id, 7)
        self.assertEqual(new.requester, "cust@example.com")
        self.assertIs(store.get(new.id), new)
        self.assertEqual(len(store.all()), 2)

    def test_sync_carries_on_after_rate_limit(self):
        sync = CrmSync(Client(fail_first=RateLimited(30)))
        self.assertEqual(sync.run([], 0), "backoff")
        self.assertEqual(sync.run([], 10), "backoff")
        self.assertEqual(sync.run([], 31), "ok")
        self.assertFalse(sync.syncing)

    def test_senior_takes_escalated_ticket(self):
        t = opened()
        actions.escalate(t, "angry")
        senior = Agent("sam", senior=True)
        actions.take(t, senior)
        self.assertEqual((t.state, t.assignee), ("open", "sam"))

    def test_junior_cannot_take_escalated_ticket(self):
        t = opened()
        actions.escalate(t, "angry")
        with self.assertRaises(DeskError):
            actions.take(t, Agent("jo"))
        self.assertEqual(t.state, "escalated")


class Unchanged(unittest.TestCase):
    def test_reply_to_open_or_pending_lands_on_the_ticket(self):
        store = TicketStore()
        t = opened(store, 3)
        actions.set_pending(t)
        got = email.handle_reply(store, "cust@example.com", "Re: [#3] printer jam", "here", 9)
        self.assertIs(got, t)
        self.assertEqual(t.state, "open")
        self.assertEqual(len(store.all()), 1)

    def test_reopen_from_solved_only(self):
        t = opened()
        actions.solve(t, 5)
        actions.reopen(t)
        self.assertEqual(t.state, "open")
        actions.solve(t, 6)
        actions.close(t)
        with self.assertRaises(DeskError):
            actions.reopen(t)

    def test_fax_tickets_stay_out_of_the_report(self):
        store = TicketStore()
        partner_api.create(store, {"subject": "fax", "requester": "f@x", "channel": "fax"}, 0)
        partner_api.create(store, {"subject": "web", "requester": "w@x"}, 0)
        self.assertEqual(report.counts(store.all(), 10)["received"], 1)

    def test_every_notification_mix(self):
        a = Agent("cy")
        for d in (True, False):
            for m in (True, False):
                a.set_notifications(d, m)
                self.assertEqual(notify.channels(a), [c for c, on in (("desktop", d), ("mobile", m)) if on])

    def test_sync_error_then_ok(self):
        from desk.crm.sync import CrmError
        sync = CrmSync(Client(fail_first=CrmError("down")))
        self.assertEqual(sync.run([], 0), "error")
        self.assertEqual(sync.run([], 1), "ok")

    def test_take_new_ticket(self):
        t = Ticket(1, "x", "c@x")
        actions.take(t, Agent("sam", senior=True))
        self.assertEqual(t.state, "open")

    def test_kb_and_webhooks(self):
        art = kb.Article("a", "A", "ann")
        art.body = "x"
        kb.submit(art)
        kb.send_back(art)
        self.assertEqual(art.status, "draft")
        d = webhooks.Delivery("http://x", {})
        webhooks.attempt(d, lambda u, e: 500)
        webhooks.attempt(d, lambda u, e: 200)
        self.assertEqual(d.status, "sent")


if __name__ == "__main__":
    unittest.main()
