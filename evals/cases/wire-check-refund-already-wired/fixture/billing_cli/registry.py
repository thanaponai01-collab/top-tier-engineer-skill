"""Commands register themselves; every module in billing_cli/commands/ is loaded on first use."""
import importlib
import pkgutil

_COMMANDS = {}


def command(name):
    def register(fn):
        _COMMANDS[name] = fn
        return fn
    return register


def all_commands():
    from billing_cli import commands
    for mod in pkgutil.iter_modules(commands.__path__):
        importlib.import_module(f"{commands.__name__}.{mod.name}")
    return dict(_COMMANDS)
