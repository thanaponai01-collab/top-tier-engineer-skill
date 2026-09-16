class Provider:
    """Send a message. Implemented once, by SmtpProvider."""

    def send(self, to, body):
        raise NotImplementedError
