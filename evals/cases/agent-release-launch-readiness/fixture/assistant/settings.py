"""Settings, loaded once when the process starts."""
import glob, os
import yaml

_HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(_HERE, "config.yaml")) as fh:
    CONFIG = yaml.safe_load(fh)

ENABLED = CONFIG["enabled"]


def prompt_path():
    if CONFIG["prompt"] == "latest":
        return sorted(glob.glob(os.path.join(_HERE, "prompts", "*.md")))[-1]
    return os.path.join(_HERE, "prompts", CONFIG["prompt"] + ".md")
