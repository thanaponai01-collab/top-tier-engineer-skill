import importlib

from settings import ENABLED_PLUGINS

_handlers = []


def load_enabled():
    for name in ENABLED_PLUGINS:
        _handlers.append(importlib.import_module(name))


def emit(event, payload):
    for h in _handlers:
        h.on_event(event, payload)
