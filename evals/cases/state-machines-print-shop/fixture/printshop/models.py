class OrderError(Exception):
    pass


class Order:
    def __init__(self, oid, customer, pages, created_at):
        self.id = oid
        self.customer = customer
        self.pages = pages
        self.created_at = created_at
        self.status = "draft"
        self.paid_at = None
        self.refunded = False

    def to_dict(self):
        return {"id": self.id, "customer": self.customer, "pages": self.pages,
                "created_at": self.created_at, "status": self.status,
                "paid_at": self.paid_at, "refunded": self.refunded}

    @classmethod
    def from_dict(cls, d):
        o = cls(d["id"], d["customer"], d["pages"], d["created_at"])
        o.status = d["status"]
        o.paid_at = d.get("paid_at")
        o.refunded = d.get("refunded", False)
        return o


class Customer:
    def __init__(self, name, email=None, phone=None):
        self.name = name
        self.email = email
        self.phone = phone
        self.notify_email = email is not None
        self.notify_sms = phone is not None

    def set_prefs(self, email_on, sms_on):
        self.notify_email = bool(email_on) and self.email is not None
        self.notify_sms = bool(sms_on) and self.phone is not None
