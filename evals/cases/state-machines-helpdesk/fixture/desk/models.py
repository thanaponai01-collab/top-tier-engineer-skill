class DeskError(Exception):
    pass


class Ticket:
    def __init__(self, tid, subject, requester, channel="web", created_at=0):
        self.id = tid
        self.subject = subject
        self.requester = requester
        self.channel = channel
        self.state = "new"
        self.assignee = None
        self.priority = "normal"
        self.tags = set()
        self.comments = []
        self.created_at = created_at
        self.solved_at = None
        self.first_reply_at = None
        self.parent_id = None

    def to_dict(self):
        d = dict(self.__dict__)
        d["tags"] = sorted(self.tags)
        return d

    @classmethod
    def from_dict(cls, d):
        t = cls(d["id"], d["subject"], d["requester"], d.get("channel", "web"), d.get("created_at", 0))
        t.state = d["state"]
        t.assignee = d.get("assignee")
        t.priority = d.get("priority", "normal")
        t.tags = set(d.get("tags", []))
        t.comments = list(d.get("comments", []))
        t.solved_at = d.get("solved_at")
        t.first_reply_at = d.get("first_reply_at")
        t.parent_id = d.get("parent_id")
        return t


class Agent:
    def __init__(self, name, role="agent", senior=False):
        self.name = name
        self.role = role
        self.senior = senior
        self.presence = "offline"
        self.last_seen = 0
        self.load = 0
        self.notify_desktop = True
        self.notify_mobile = False

    def set_notifications(self, desktop, mobile):
        self.notify_desktop = bool(desktop)
        self.notify_mobile = bool(mobile)
