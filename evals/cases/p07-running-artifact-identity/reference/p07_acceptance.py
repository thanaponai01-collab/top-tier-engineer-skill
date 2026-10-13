"""Independent replay: unchanged identity passes; stale source/runtime is rejected."""
import json
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parent


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def start(root):
    proc = subprocess.Popen([sys.executable, "app.py", "serve"], cwd=root,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    settings = json.loads((root / "config.json").read_text(encoding="utf-8"))
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        try:
            with urlopen(f"http://127.0.0.1:{settings['port']}/identity", timeout=.2) as response:
                json.load(response)
            return proc
        except Exception:
            if proc.poll() is not None:
                raise AssertionError("identity service exited before ready")
            time.sleep(.03)
    proc.terminate()
    proc.wait(timeout=3)
    raise AssertionError("identity service did not become ready")


def doctor(root, expected):
    proc = subprocess.run([sys.executable, "doctor.py"], cwd=root, capture_output=True,
                          text=True, timeout=5)
    if (proc.returncode == 0) != expected:
        raise AssertionError(f"doctor exit {proc.returncode}, expected {expected}: {proc.stdout}{proc.stderr}")
    return proc.stdout + proc.stderr


def main():
    for changed in (None, "source", "flags", "role", "mocks"):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "current"
            old = Path(temp) / "old"
            shutil.copytree(ROOT, root, ignore=shutil.ignore_patterns(
                "p07_acceptance.py", "__pycache__", ".verify-run", ".verify-state.json", ".verify-evidence"))
            settings = json.loads((root / "config.json").read_text(encoding="utf-8"))
            settings["port"] = free_port()
            (root / "config.json").write_text(json.dumps(settings, sort_keys=True), encoding="utf-8")
            shutil.copytree(root, old)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            subprocess.run(["git", "-C", str(root), "config", "user.email", "p07@example.test"], check=True)
            subprocess.run(["git", "-C", str(root), "config", "user.name", "P07 Test"], check=True)
            subprocess.run(["git", "-C", str(root), "add", "app.py", "config.json"], check=True)
            subprocess.run(["git", "-C", str(root), "commit", "-qm", "fixture"], check=True)
            head = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
            server = start(root if changed is None else old)
            try:
                if changed is None:
                    output = doctor(root, True)
                    for field in ("source_sha256", "config_sha256", "flags", "role", "mocks"):
                        if field not in output:
                            raise AssertionError(f"doctor evidence omits {field}")
                    continue
                if changed == "source":
                    with (root / "app.py").open("a", encoding="utf-8") as stream:
                        stream.write("\n# uncommitted source revision\n")
                else:
                    settings[changed] = ["--mode=staging"] if changed == "flags" else ("worker" if changed == "role" else ["mail-live"])
                    (root / "config.json").write_text(json.dumps(settings, sort_keys=True), encoding="utf-8")
                output = doctor(root, False)
                current_head = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
                if current_head != head:
                    raise AssertionError("HEAD changed during the uncommitted identity replay")
                expected = {"source": "source_sha256", "flags": "flags", "role": "role", "mocks": "mocks"}[changed]
                if expected not in output:
                    raise AssertionError(f"doctor did not name changed identity field {expected}: {output}")
                with urlopen(f"http://127.0.0.1:{settings['port']}/identity", timeout=1) as response:
                    if json.load(response)["pid"] != server.pid:
                        raise AssertionError("control process was not the healthy old process")
                print(f"rejected healthy stale process: {changed}")
            finally:
                if server.poll() is None:
                    server.terminate()
                    server.wait(timeout=3)
    print("current identity passes; stale source and all runtime contract fields reject")


if __name__ == "__main__":
    main()
