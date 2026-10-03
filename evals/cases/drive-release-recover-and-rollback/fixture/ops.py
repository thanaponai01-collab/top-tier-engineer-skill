"""Local-only provider simulator: deploy can apply before losing its response."""
import json
from pathlib import Path
import sys


def state():
    return json.loads(Path("remote.json").read_text())


def save(value):
    Path("remote.json").write_text(json.dumps(value))


if __name__ == "__main__":
    operation = sys.argv[1]
    remote = state()
    if operation == "deploy":
        remote["deploy_calls"] += 1
        if remote["version"] == "v2":
            save(remote)
            sys.exit("duplicate deployment refused")
        Path("remote_app.py").write_bytes(Path("app.py").read_bytes())
        remote["version"] = "v2"
        save(remote)
        sys.exit("provider response lost; release status unknown to caller")
    elif operation == "rollback":
        remote["rollback_calls"] += 1
        Path("remote_app.py").write_bytes(Path("v1.py").read_bytes())
        remote["version"] = "v1"
        save(remote)
        print("restored v1")
    elif operation == "probe-deploy":
        print(remote["version"])
        sys.exit(0 if remote["version"] == "v2" else 3)
    elif operation == "probe-rollback":
        print(remote["version"])
        sys.exit(0 if remote["version"] == "v1" and remote["rollback_calls"] else 3)
    else:
        sys.exit("unsupported operation")
