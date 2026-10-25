#!/usr/bin/env python3
"""
wire.py - the call-trace snapshot and the three stages behind wire-check.

Each test plants the thing a stage exists to catch, so disabling that part of the gate turns it red.
Run them all with `python -m unittest discover tests`.
"""
import json, os, subprocess, sys, tempfile, unittest

from _helpers import run, SCRIPTS

FEATURES = os.path.join(SCRIPTS["features.py"], "features.py")
VERIFY = os.path.join(SCRIPTS["verify.py"], "verify.py")

APP = {
    "pyproject.toml": '[project]\nname = "shop"\n\n[project.scripts]\nshop = "shop:main"\nshop-admin = "admin:main"\n',
    "shop.py": (
        "import sys\nimport app.handlers  # noqa: F401\nfrom app import inventory\n\n\n"
        "def main(argv=None):\n    argv = sys.argv[1:] if argv is None else argv\n"
        "    inventory.change(argv[0], -int(argv[1]))\n    return 0\n\n\n"
        "if __name__ == \"__main__\":\n    sys.exit(main())\n"),
    "admin.py": "def main():\n    print('admin')\n\n\nif __name__ == \"__main__\":\n    main()\n",
    "app/__init__.py": "",
    "app/bus.py": (
        "_subs = {}\n\n\ndef subscribe(event):\n    def reg(fn):\n        _subs.setdefault(event, []).append(fn)\n"
        "        return fn\n    return reg\n\n\ndef publish(event, **payload):\n"
        "    for fn in _subs.get(event, []):\n        try:\n            fn(**payload)\n"
        "        except Exception:\n            pass\n"),
    "app/inventory.py": (
        "import json\nfrom app import bus\n\n\ndef change(sku, delta):\n"
        "    stock = json.load(open('stock.json'))\n    stock[sku] += delta\n"
        "    json.dump(stock, open('stock.json', 'w'))\n"
        "    bus.publish('stock.changed', sku=sku, qty=stock[sku])\n\n\n"
        "def legacy_recount():\n    return 0\n"),
    "app/handlers/__init__.py": "from . import audit\n",
    "app/handlers/audit.py": (
        "from app.bus import subscribe\n\n\n@subscribe('stock.changed')\ndef record(sku, qty, **_):\n"
        "    open('audit.log', 'a').write(f'{sku} {qty}\\n')\n"),
    "app/handlers/alert.py": (
        "from app.bus import subscribe\n\n\n@subscribe('stock.changed')\ndef alert(sku, quantity, **_):\n"
        "    if quantity < 5:\n        open('alerts.log', 'a').write(f'LOW {sku}\\n')\n"),
    "stock.json": '{"widget": 12}\n',
}
RUNS = ["--run", "python shop.py widget 9", "--run", "python admin.py"]


def make(tmp, files=APP):
    for rel, text in files.items():
        p = os.path.join(tmp, *rel.split("/"))
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)


def snapshot(tmp):
    with open(os.path.join(tmp, ".wire", "snapshot.json"), encoding="utf-8") as fh:
        return json.load(fh)


def entered(tmp):
    return {k for r in snapshot(tmp)["results"].values() for k in r["entered"]}


def edit(tmp, rel, old, new):
    p = os.path.join(tmp, *rel.split("/"))
    with open(p, encoding="utf-8") as fh:
        text = fh.read()
    assert old in text, (rel, old)
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text.replace(old, new))


def fill(tmp, lines):
    p = os.path.join(tmp, ".wire", "verdicts.md")
    with open(p, encoding="utf-8") as fh:
        keep = [ln for ln in fh.read().splitlines() if "[[fill" not in ln]
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(keep + lines) + "\n")


class Snapshot(unittest.TestCase):
    def test_records_functions_entered_through_subprocesses_not_files_loaded(self):
        """A live file's dead helper is unentered while its sibling ran: an import graph calls the
        whole file live; the tracer does not."""
        with tempfile.TemporaryDirectory() as tmp:
            make(tmp)
            code, out, err = run("wire.py", tmp, "--snapshot", "--run", "python shop.py widget 9")
            self.assertEqual(code, 0, out + err)
            seen = entered(tmp)
            self.assertIn("app/inventory.py::change", seen)
            self.assertIn("app/handlers/audit.py::record", seen)
            self.assertNotIn("app/inventory.py::legacy_recount", seen)

    def test_a_call_with_the_wrong_arguments_is_not_entered(self):
        """alert takes `quantity` but is sent `qty`: the bus swallows the TypeError, and the handler
        never runs. It must not count as reached."""
        with tempfile.TemporaryDirectory() as tmp:
            make(tmp)
            edit(tmp, "app/handlers/__init__.py", "import audit", "import audit, alert")
            run("wire.py", tmp, "--snapshot", "--run", "python shop.py widget 9")
            self.assertNotIn("app/handlers/alert.py::alert", entered(tmp))
            edit(tmp, "app/handlers/alert.py", "quantity", "qty")
            run("wire.py", tmp, "--snapshot", "--run", "python shop.py widget 9")
            self.assertIn("app/handlers/alert.py::alert", entered(tmp))

    def test_commands_run_in_a_copy_so_the_data_is_untouched(self):
        with tempfile.TemporaryDirectory() as tmp:
            make(tmp)
            run("wire.py", tmp, "--snapshot", "--run", "python shop.py widget 9")
            self.assertEqual(open(os.path.join(tmp, "stock.json")).read(), '{"widget": 12}\n')
            self.assertFalse(os.path.exists(os.path.join(tmp, "audit.log")))

    def test_a_snapshot_after_a_change_keeps_the_first_as_before(self):
        with tempfile.TemporaryDirectory() as tmp:
            make(tmp)
            run("wire.py", tmp, "--snapshot", "--run", "python shop.py widget 9")
            first = snapshot(tmp)
            edit(tmp, "app/handlers/__init__.py", "import audit", "import audit, alert")
            run("wire.py", tmp, "--snapshot", "--run", "python shop.py widget 9")
            edit(tmp, "app/handlers/alert.py", "quantity", "qty")
            run("wire.py", tmp, "--snapshot", "--run", "python shop.py widget 9")
            with open(os.path.join(tmp, ".wire", "before.json"), encoding="utf-8") as fh:
                self.assertEqual(json.load(fh)["shas"], first["shas"])


class Gate(unittest.TestCase):
    def test_stage1_every_declared_way_in_must_be_started_or_excused(self):
        with tempfile.TemporaryDirectory() as tmp:
            make(tmp)
            code, out, _ = run("wire.py", tmp, "--gate", "--run", "python shop.py widget 9")
            self.assertEqual(code, 1)
            self.assertIn("console script `shop-admin` (admin.py) was never started", out)
            self.assertNotIn("`shop` (shop.py) was never started", out)
            os.makedirs(os.path.join(tmp, ".wire"), exist_ok=True)
            with open(os.path.join(tmp, ".wire", "verdicts.md"), "a", encoding="utf-8") as fh:
                fh.write("- entry shop-admin: not run: needs the operator's VPN\n"
                         "- entry admin.py: not run: same script as shop-admin\n")
            _, out, _ = run("wire.py", tmp, "--gate")
            self.assertIn("STAGE 1 snapshot: current, every way in started: holds", out)

    def test_stage1_a_snapshot_older_than_the_code_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            make(tmp)
            run("wire.py", tmp, "--snapshot", *RUNS)
            edit(tmp, "app/inventory.py", "return 0", "return 1")
            _, out, _ = run("wire.py", tmp, "--gate")
            self.assertIn("code changed since the snapshot (app/inventory.py)", out)

    def test_stage2_every_unentered_function_needs_a_cited_verdict(self):
        with tempfile.TemporaryDirectory() as tmp:
            make(tmp)
            code, out, _ = run("wire.py", tmp, "--gate", *RUNS)
            self.assertEqual(code, 1)
            with open(os.path.join(tmp, ".wire", "verdicts.md"), encoding="utf-8") as fh:
                slots = fh.read()
            self.assertIn("- app/inventory.py::legacy_recount: [[fill:", slots)   # one function of a live file
            self.assertIn("- app/handlers/alert.py: [[fill:", slots)              # a whole unentered file
            fill(tmp, ["- app/inventory.py::legacy_recount: never-invoked: nothing calls it, see app/inventory.py:99",
                       "- app/handlers/alert.py: not-registered: app/handlers/__init__.py imports only audit"])
            _, out, _ = run("wire.py", tmp, "--gate")
            self.assertIn("cites app/inventory.py:99, past the end of the file", out)
            fill(tmp, ["- app/inventory.py::legacy_recount: never-invoked: nothing calls it"])
            _, out, _ = run("wire.py", tmp, "--gate")
            self.assertIn("`never-invoked` needs the file:line it rests on", out)
            fill(tmp, ["- app/inventory.py::legacy_recount: not-registered: no caller anywhere in the repo"])
            code, out, _ = run("wire.py", tmp, "--gate")
            self.assertEqual(code, 0, out)
            self.assertIn("not-registered (2):", out)
            self.assertIn("WIRE-GATE: done(", out)

    def test_stage2_a_file_verdict_does_not_cover_a_file_that_partly_ran(self):
        with tempfile.TemporaryDirectory() as tmp:
            make(tmp)
            run("wire.py", tmp, "--gate", *RUNS)
            fill(tmp, ["- app/handlers/alert.py: not-registered: app/handlers/__init__.py imports only audit",
                       "- app/inventory.py: not-registered: whole file, wrongly"])
            code, out, _ = run("wire.py", tmp, "--gate")
            self.assertEqual(code, 0, out)   # a file line covers the unentered functions of that file ...
            self.assertIn("app/inventory.py", out)
            self.assertNotIn("app/inventory.py::change", out.split("ANSWER")[1])   # ... not the ones that ran


class Keep(unittest.TestCase):
    """Stage 3: a component connected in this task is entered by a real command now, mapped in
    FEATURES.md and checked by a VERIFY.md section seen rejecting the broken wiring."""

    def connect(self, tmp):
        edit(tmp, "app/handlers/__init__.py", "import audit", "import audit, alert")
        edit(tmp, "app/handlers/alert.py", "quantity", "qty")

    def test_keep_needs_the_target_entered_mapped_and_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            make(tmp)
            target = ["--target", "app/handlers/alert.py::alert"]
            code, out, _ = run("wire.py", tmp, "--gate", *RUNS, *target)
            self.assertEqual(code, 1)
            self.assertIn("app/handlers/alert.py::alert: no snapshot command entered it", out)
            self.connect(tmp)
            code, out, _ = run("wire.py", tmp, "--gate", *RUNS)       # targets are remembered
            self.assertNotIn("no snapshot command entered it", out)
            self.assertIn("no FEATURES.md feature traces to it", out)
            self.assertIn("no VERIFY.md section has app/handlers/alert.py in its `path:`", out)

            # the map: a trace ending in the handler's file, its entry point proven
            make(tmp, {"FEATURES.md": (
                "## Low-stock alert\n- what: Warn when a sale takes a shelf under 5.\n"
                "- cli: `widget` @ shop.py :: argv\n"
                "- trace: `main` @ shop.py > `change` @ app/inventory.py > `stock.changed` @ app/handlers/alert.py\n"
                "- verify: Low-stock alert\n- status: proven: sold 9, alert written\n"),
                "AGENTS.md": "Read FEATURES.md first. After any change: `python .features/features.py check --rerun`\n",
                "checks/check_alert.py": (
                    "import os, shutil, subprocess, sys, tempfile\n"
                    "here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))\n"
                    "t = os.path.join(tempfile.mkdtemp(), 'r')\n"
                    "shutil.copytree(here, t, ignore=shutil.ignore_patterns('.wire', '.features', '__pycache__', 'alerts.log'))\n"
                    "subprocess.run([sys.executable, 'shop.py', 'widget', '9'], cwd=t, check=True)\n"
                    "if not os.path.exists(os.path.join(t, 'alerts.log')):\n"
                    "    print('no low-stock alert written'); sys.exit(1)\n"),
                "VERIFY.md": ("## Low-stock alert\n- path: app/handlers/, shop.py\n- run: `python checks/check_alert.py`\n"
                              "- oracle: checks/check_alert.py\n- fail-signal: no low-stock alert written\n")})
            subprocess.run([sys.executable, FEATURES, "prove", "--repo", tmp, "--feature", "Low-stock alert",
                            "--entry", "cli: widget", "--copy", "--", sys.executable, "shop.py", "widget", "9"],
                           capture_output=True, text=True)
            _, out, _ = run("wire.py", tmp, "--gate")
            self.assertNotIn("FEATURES.md", out.split("STAGE 3")[1].split("WIRE-GATE")[0], out)
            self.assertIn("has no rejection receipt", out)   # green alone is not a receipt

            # the receipt: the check run red on the broken wiring, then green on the repair
            edit(tmp, "app/handlers/__init__.py", "import audit, alert", "import audit")
            subprocess.run([sys.executable, VERIFY, "run", tmp], capture_output=True, text=True)
            edit(tmp, "app/handlers/__init__.py", "import audit", "import audit, alert")
            with open(os.path.join(tmp, "VERIFY.md"), "a", encoding="utf-8") as fh:
                fh.write("- fail-proof: dropped alert from app/handlers/__init__.py, no alert written, restored\n")
            subprocess.run([sys.executable, VERIFY, "run", tmp], capture_output=True, text=True)
            fill(tmp, ["- app/inventory.py::legacy_recount: not-registered: no caller anywhere in the repo",
                       "- entry shop-admin: not run: x", "- entry admin.py: not run: x"])
            code, out, _ = run("wire.py", tmp, "--gate")
            self.assertEqual(code, 0, out)
            self.assertIn("the snapshot before the change never entered it", out)
            self.assertIn("1 connected", out)

    def test_the_wire_ledger_does_not_make_verify_loop_stale(self):
        """The gate writes .wire/ after verify.py runs; that is evidence, not product."""
        with tempfile.TemporaryDirectory() as tmp:
            make(tmp)
            make(tmp, {"VERIFY.md": "## Stock\n- path: app/\n- run: `python shop.py widget 1`\n"})
            subprocess.run([sys.executable, VERIFY, "run", tmp], capture_output=True, text=True)
            make(tmp, {".wire/targets.json": "[]"})
            p = subprocess.run([sys.executable, VERIFY, "status", tmp], capture_output=True, text=True)
            self.assertNotIn("stale", p.stdout)


if __name__ == "__main__":
    unittest.main()
