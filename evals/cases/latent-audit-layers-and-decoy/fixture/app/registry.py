"""Resolves plugins by name at runtime. No static import reaches them."""
import importlib

ENABLED_PLUGINS = ["app.plugins.csv_out"]


def load():
    return [importlib.import_module(name) for name in ENABLED_PLUGINS]
