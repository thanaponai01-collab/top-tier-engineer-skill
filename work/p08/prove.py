import subprocess
import sys

commands = [
    [sys.executable, "-m", "unittest", "discover", "tests"],
    [sys.executable, "tools/catalog.py", "--check"],
]
for command in commands:
    result = subprocess.run(command, check=False)
    if result.returncode:
        raise SystemExit(result.returncode)
