from providers.base import Provider


class SmtpProvider(Provider):
    def send(self, to, body):
        return f"smtp:{to}:{body}"
