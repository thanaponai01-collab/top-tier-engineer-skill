"""Grader's outcome check, run in the agent's finished folder.

Works on a scratch copy with the original orders, so whatever the agent did to data/ does not
matter. Checks: the ask (total is computed once while an order is unchanged), and every command
still does what it did before the change.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ORDERS = [
    {"id": "A-1001", "customer": "acme", "status": "open", "lines": [
        {"id": "L1", "sku": "WIDGET", "price_cents": 1250, "qty": 4},
        {"id": "L2", "sku": "GADGET", "price_cents": 8999, "qty": 1},
        {"id": "L3", "sku": "CABLE", "price_cents": 399, "qty": 10}]},
    {"id": "A-1002", "customer": "globex", "status": "open", "lines": [
        {"id": "L1", "sku": "GADGET", "price_cents": 8999, "qty": 3}]},
    {"id": "A-1003", "customer": "acme", "status": "open", "lines": [
        {"id": "L1", "sku": "MOUNT", "price_cents": 2450, "qty": 2},
        {"id": "L2", "sku": "CABLE", "price_cents": 399, "qty": 6}]},
    {"id": "A-1004", "customer": "initech", "status": "open", "lines": [
        {"id": "L1", "sku": "WIDGET", "price_cents": 1250, "qty": 20},
        {"id": "L2", "sku": "MOUNT", "price_cents": 2450, "qty": 4}]},
    {"id": "A-1005", "customer": "globex", "status": "open", "lines": [
        {"id": "L1", "sku": "SCREEN", "price_cents": 15900, "qty": 1},
        {"id": "L2", "sku": "CABLE", "price_cents": 399, "qty": 2}]},
]
DASHBOARD = """Top orders:
  A-1004  initech       $348.00  33.5%
  A-1002  globex        $269.97  26.0%
  A-1001  acme          $179.89  17.3%
Customers:
  globex        $436.95
  initech       $348.00
  acme          $252.83"""
LIST_AFTER_REFUND = """A-1001  acme       partly refunded      $89.90
A-1002  globex     open                $269.97
A-1003  acme       open                 $72.94
A-1004  initech    open                $348.00
A-1005  globex     open                $166.98"""

failures = []


def fresh():
    work = tempfile.mkdtemp(prefix="em-check-")
    dst = os.path.join(work, "app")
    shutil.copytree(HERE, dst, ignore=shutil.ignore_patterns("__pycache__", ".git"))
    with open(os.path.join(dst, "data", "orders.json"), "w", encoding="utf-8") as f:
        json.dump(ORDERS, f, indent=2)
    return dst


def shop(app, *args):
    p = subprocess.run([sys.executable, "shop.py", *args], cwd=app, capture_output=True, text=True,
                       timeout=60)
    return p.returncode, (p.stdout + p.stderr).strip()


def expect(name, ok, detail=""):
    print(("ok    " if ok else "FAIL  ") + name + ("" if ok else f"\n      {detail}"))
    if not ok:
        failures.append(name)


# 1. The ask: Order.total computed once while the order is unchanged.
app = fresh()
probe = (
    "import sys; sys.path.insert(0, '.')\n"
    "import store\nfrom orders import model\n"
    "calls = [0]\norig = model.Line.subtotal\n"
    "def counted(self):\n    calls[0] += 1\n    return orig(self)\n"
    "model.Line.subtotal = counted\n"
    "orders = store.load_orders()\n"
    "lines = sum(len(o.lines) for o in orders)\n"
    "for _ in range(20):\n    [o.total for o in orders]\n"
    "print(calls[0], lines)\n"
)
p = subprocess.run([sys.executable, "-c", probe], cwd=app, capture_output=True, text=True, timeout=60)
try:
    calls, lines = map(int, p.stdout.split())
    expect("total is cached: 20 reads of every order cost at most 2 sums", calls <= 2 * lines,
           f"Line.subtotal ran {calls} times for {lines} lines")
except ValueError:
    expect("total is cached", False, (p.stdout + p.stderr).strip()[-400:])

# 2. Dashboard unchanged.
code, out = shop(app, "dashboard")
expect("dashboard prints what it printed before", code == 0 and out == DASHBOARD, out[-400:])

# 3. Refund: the receipt and the stored order show the new total.
app = fresh()
code, out = shop(app, "refund", "A-1001", "L2")
expect("refund receipt shows the new total $89.90",
       code == 0 and "New total $89.90." in out and "total before refund: $179.89" in out, out[-400:])
code, out = shop(app, "list")
expect("after a refund, list shows A-1001 partly refunded at $89.90",
       code == 0 and out == LIST_AFTER_REFUND, out[-400:])

# 4. Backup, then restore, still round-trips.
app = fresh()
code, out = shop(app, "backup", "b.json")
expect("backup runs", code == 0 and "Backed up 5 orders worth $1,037.78" in out, out[-400:])
code, out = shop(app, "restore", "b.json")
expect("restore reads the backup back", code == 0 and "Restored 5 orders" in out, out[-400:])
code, out = shop(app, "dashboard")
expect("dashboard after restore prints what it printed before", code == 0 and out == DASHBOARD,
       out[-400:])

# 5. A refund after a restore, on orders that went through the backup path.
code, out = shop(app, "refund", "A-1001", "L2")
expect("refund after restore shows the new total", code == 0 and "New total $89.90." in out,
       out[-400:])

sys.exit(1 if failures else 0)
