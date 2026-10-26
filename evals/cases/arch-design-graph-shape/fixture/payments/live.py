class LiveGateway:
    def charge(self, customer_id, cents):
        return f'live-{customer_id}-{cents}'

    def refund(self, charge_id, cents):
        return f'live-refund-{charge_id}-{cents}'
