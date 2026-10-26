from providers.smtp import SmtpProvider

PROVIDERS = {"smtp": SmtpProvider}


def get(name="smtp"):
    return PROVIDERS[name]()
