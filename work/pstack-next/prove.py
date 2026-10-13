import subprocess
import sys

for command in ([sys.executable, "-m", "unittest", "discover", "tests"], [sys.executable, "tools/catalog.py", "--check"]):
    result = subprocess.run(command, text=True, capture_output=True)
    output = result.stdout + result.stderr
    print(output, end="")
    if result.returncode:
        raise SystemExit(result.returncode)
