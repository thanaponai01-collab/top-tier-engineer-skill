import unittest

from desk import automations, kb, notify, presence, webhooks
from desk.models import Agent, DeskError, Ticket
from desk.tickets import actions


def opened(tid=1):
    t = Ticket(tid, "printer jam", "cust@example.com")
    actions.assign(t, Agent("ann"))
    return t


class Tickets(unittest.TestCase):
    def test_assign_opens(self):
        t = opened()
        self.assertEqual((t.state, t.assignee), ("open", "ann"))

    def test_pending_and_back(self):
        t = opened()
        actions.set_pending(t)
        actions.customer_replied(t, "here you go", 10)
        self.assertEqual(t.state, "open")

    def test_solve_close(self):
        t = opened()
        actions.solve(t, 5)
        actions.close(t)
        self.assertEqual(t.state, "closed")

    def test_reopen_only_from_solved(self):
        t = opened()
        actions.solve(t, 5)
        actions.reopen(t)
        self.assertEqual(t.state, "open")
        actions.solve(t, 6)
        actions.close(t)
        with self.assertRaises(DeskError):
            actions.reopen(t)

    def test_auto_close(self):
        t = opened()
        actions.solve(t, 0)
        self.assertEqual(automations.run([t], 5 * 24 * 3600)["closed"], [1])


class Other(unittest.TestCase):
    def test_presence(self):
        a = Agent("bo")
        presence.go_online(a, 0)
        self.assertEqual(presence.sweep([a], 1000), ["bo"])

    def test_kb_flow(self):
        art = kb.Article("reset", "Reset your password", "ann")
        art.body = "Click reset."
        kb.submit(art)
        kb.approve(art, "bo")
        self.assertEqual(kb.visible([art]), [art])

    def test_webhook_gives_up(self):
        d = webhooks.Delivery("http://x", {})
        for _ in range(5):
            webhooks.attempt(d, lambda u, e: 500)
        self.assertEqual(d.status, "dead")

    def test_notify(self):
        a = Agent("cy")
        a.set_notifications(False, True)
        self.assertEqual(notify.channels(a), ["mobile"])


if __name__ == "__main__":
    unittest.main()
