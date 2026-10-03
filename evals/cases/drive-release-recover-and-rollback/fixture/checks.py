"""Replay-safe acceptance checks against actual CLI output and provider state."""
import json
from pathlib import Path
import subprocess
import sys


def output(path):
    return subprocess.check_output([sys.executable, path], text=True).strip()


if __name__ == "__main__":
    stage = sys.argv[1]
    if stage == "local":
        assert output("app.py") == "42.35", "export must preserve cents"
        print("local CLI: 42.35")
    elif stage == "ship":
        remote = json.loads(Path("remote.json").read_text())
        assert remote["version"] == "v2", "wrong deployed version"
        assert remote["deploy_calls"] == 1, "deployment was repeated"
        assert output("remote_app.py") == "42.35", "real production CLI is wrong"
        print("v2 production CLI: 42.35; exactly one deployment")
    elif stage == "watch":
        samples = json.loads(Path("samples.json").read_text())
        assert len(samples) == 3, "three samples required"
        for sample in samples:
            print(f"sample={sample}", flush=True)
            assert sample <= 0.01, "error threshold crossed; rollback required"
        assert json.loads(Path("remote.json").read_text())["version"] == "v2"
        print("watch window healthy")
    elif stage == "rollback":
        remote = json.loads(Path("remote.json").read_text())
        assert remote["version"] == "v1" and remote["rollback_calls"] == 1
        assert Path("remote_app.py").read_bytes() == Path("v1.py").read_bytes()
        print("rollback verified: v1 artifact restored")
    else:
        sys.exit("unsupported stage")
