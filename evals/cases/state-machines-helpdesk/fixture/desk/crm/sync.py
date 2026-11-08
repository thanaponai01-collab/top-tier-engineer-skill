"""Pushes ticket changes to the CRM every minute (run by the scheduler)."""


class CrmError(Exception):
    pass


class RateLimited(CrmError):
    def __init__(self, retry_after):
        super().__init__(f"rate limited, retry after {retry_after}s")
        self.retry_after = retry_after


class CrmSync:
    def __init__(self, client):
        self.client = client
        self.syncing = False
        self.last_error = None
        self.backoff_until = 0
        self.pushed = 0

    def run(self, tickets, now):
        if now < self.backoff_until:
            return "backoff"
        if self.syncing:
            return "busy"
        self.syncing = True
        batch = [t.to_dict() for t in tickets]
        try:
            self.client.push(batch)
        except RateLimited as e:
            self.backoff_until = now + e.retry_after
            return "backoff"
        except CrmError as e:
            self.last_error = str(e)
            self.syncing = False
            return "error"
        self.pushed += len(batch)
        self.last_error = None
        self.syncing = False
        return "ok"
