class FakeGateway:
    def __init__(self):
        self.log = []

    def charge(self, customer_id, cents):
        self.log.append(('charge', customer_id, cents))
        return f'fake-{len(self.log)}'

    def refund(self, charge_id, cents):
        self.log.append(('refund', charge_id, cents))
        return f'fake-refund-{len(self.log)}'
