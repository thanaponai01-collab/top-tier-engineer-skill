import importlib

import settings


def load():
    for name in settings.INTEGRATIONS:
        importlib.import_module(f"integrations.{name}")
