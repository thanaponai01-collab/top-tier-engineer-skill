"""The one answer every caller gets: verdict, VERIFY: line, observed rejection, passes and gaps."""
import json, os, stat, shutil, tempfile, unittest

from _helpers import run, ROOT

FLAG = "python -c \"import os,sys; os.path.exists('ok.flag') or (print('expected ok.flag present'), sys.exit(1))\""
BROKEN = "python -c \"import nosuchmodule_xyz\""


def write(root, rel, text=""):
    p = os.path.join(root, *rel.split("/"))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def recipe(cmd=FLAG, signal="expected ok.flag present"):
    return (f"## Thing\n- test: `{cmd}`\n- fail-signal: {signal}\n- fail-proof: deleted ok.flag, check went red\n\n"
            "## Bare\n\n## Blind spots\n- the network is stubbed\n")


def answer(tmp, *extra):
    code, out, err = run("verify.py", "status", tmp, "--json", *extra)
    return code, json.loads(out)


class Answer(unittest.TestCase):
    def test_no_recipe_is_unverified_and_silent_exit_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, a = answer(tmp)
            self.assertEqual((code, a["verdict"], a["state"]), (0, "unverified", "none"))
            self.assertEqual(a["rejections"], [])

    def test_never_run_is_unverified(self):
        with tempfile.TemporaryDirectory() as tmp:
            write(tmp, "VERIFY.md", recipe())
            code, a = answer(tmp)
            self.assertEqual((code, a["verdict"]), (3, "unverified"))
            self.assertIsNone(a["verify_line"])

    def test_observed_rejection_then_green_answer_carries_every_part(self):
        with tempfile.TemporaryDirectory() as tmp:
            write(tmp, "VERIFY.md", recipe().replace("## Bare\n\n", ""))
            run("verify.py", "run", tmp)
            code, a = answer(tmp)
            self.assertEqual((code, a["verdict"]), (1, "red"))
            self.assertEqual(a["gaps"]["failing"], [f"Thing|{FLAG}"])
            rej = a["rejections"][0]
            self.assertEqual((rej["feature"], rej["fail_signal"], rej["exit"]),
                             ("Thing", "expected ok.flag present", 1))
            self.assertEqual(rej["wrong_state"], "deleted ok.flag, check went red")
            self.assertIn("expected ok.flag present", rej["observed"])
            write(tmp, "ok.flag")
            run("verify.py", "baseline", tmp)
            run("verify.py", "run", tmp)
            code, a = answer(tmp)
            self.assertEqual((code, a["verdict"]), (3, "partial"))
            run("verify.py", "run", tmp, "--strict")
            code, a = answer(tmp)
            self.assertEqual((code, a["verdict"]), (0, "green"), a)
            self.assertTrue(a["verify_line"].startswith("VERIFY: 1 features | 1 checks pass, 0 fail"))
            self.assertEqual(a["passed"], [{"feature": "Thing", "command": FLAG}])
            self.assertEqual(a["gaps"]["blind_spots"], ["the network is stubbed"])
            self.assertEqual(len(a["rejections"]), 1)
            write(tmp, "src.py", "x = 1\n")
            code, a = answer(tmp)
            self.assertEqual((code, a["verdict"]), (3, "stale"))

    def test_report_json_equals_status_json_and_text_leads_with_verdict(self):
        with tempfile.TemporaryDirectory() as tmp:
            write(tmp, "VERIFY.md", recipe())
            run("verify.py", "run", tmp)
            code, out, _ = run("verify.py", "report", tmp, "--json")
            self.assertEqual(json.loads(out), answer(tmp)[1])
            code, out, _ = run("verify.py", "report", tmp)
            lines = out.splitlines()
            self.assertEqual(code, 1)
            self.assertTrue(lines[0].startswith("VERDICT: red"), out)
            self.assertTrue(lines[1].startswith("VERIFY: 2 features"), out)
            self.assertIn("REJECTED  Thing", out)
            self.assertIn("GAP  no check: Bare", out)
            self.assertIn("GAP  blind spot: the network is stubbed", out)

    def test_a_harness_error_or_missing_signal_is_not_a_rejection(self):
        with tempfile.TemporaryDirectory() as tmp:
            write(tmp, "VERIFY.md", recipe(BROKEN, "nosuchmodule_xyz"))
            run("verify.py", "run", tmp)
            _, a = answer(tmp)
            self.assertEqual(a["rejections"], [])
            self.assertIn("Thing", a["gaps"]["unproven"])
            self.assertIn("REJECTED  none observed", run("verify.py", "report", tmp)[1])

    def test_run_json_carries_the_verify_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            write(tmp, "VERIFY.md", recipe())
            write(tmp, "ok.flag")
            _, out, _ = run("verify.py", "run", tmp, "--json")
            line = json.loads(out)["verify_line"]
            self.assertEqual(answer(tmp)[1]["verify_line"], line)


class ScaffoldSkill(unittest.TestCase):
    def test_web_stack_with_playwright_and_features_from_verify_md(self):
        with tempfile.TemporaryDirectory() as tmp:
            write(tmp, "package.json", json.dumps({"name": "shop", "scripts": {"dev": "vite", "test": "vitest"},
                                                   "devDependencies": {"@playwright/test": "1", "vite": "5"}}))
            write(tmp, "VERIFY.md", "".join(f"## F{i}\n- test: `x`\n" for i in range(7)) +
                  "## Journey: Buy\n- features: F0, F1\n")
            code, out, _ = run("verify.py", "scaffold-skill", tmp)
            self.assertEqual(code, 0, out)
            self.assertIn("surface: web; harness: Playwright", out)
            base = os.path.join(tmp, ".claude", "skills", "verify")
            with open(os.path.join(base, "SKILL.md"), encoding="utf-8") as fh:
                skill = fh.read()
            self.assertTrue(skill.startswith("---\nname: verify\n"))
            self.assertNotIn("disable-model-invocation", skill)
            self.assertIn("`npm run dev`", skill)
            self.assertIn("../../../VERIFY.md", skill)
            feats = sorted(os.listdir(os.path.join(base, "features")))
            self.assertEqual(feats, ["README.md", "f0.md", "f1.md", "f2.md", "f3.md", "f4.md"])
            with open(os.path.join(base, "features", "f0.md"), encoding="utf-8") as fh:
                f0_text = fh.read()
            self.assertIn("verify-section: F0", f0_text)
            self.assertIn("## Driving it with Playwright", f0_text)
            code, out, _ = run("verify.py", "scaffold-skill", tmp)
            self.assertEqual(code, 1)
            self.assertIn("not overwriting", out)

    def test_detects_go_cli_rust_api_and_compose_ports(self):
        cases = [({"go.mod": "module example.com/x/tool\nrequire github.com/spf13/cobra v1\n"}, "surface: cli", "go"),
                 ({"Cargo.toml": '[package]\nname = "svc"\n[dependencies]\naxum = "0.7"\n'}, "surface: api", "rust"),
                 ({"app.py": "from http.server import HTTPServer\n"}, "surface: api", "python")]
        for files, surface, stack in cases:
            with tempfile.TemporaryDirectory() as tmp:
                for rel, text in files.items():
                    write(tmp, rel, text)
                code, out, _ = run("verify.py", "scaffold-skill", tmp)
                self.assertIn(surface, out)
                self.assertIn(stack, out)
                self.assertIn("map the top 3-5", out)
        with tempfile.TemporaryDirectory() as tmp:
            write(tmp, "compose.yaml", 'services:\n  web:\n    ports:\n      - "8080:80"\n')
            write(tmp, "Dockerfile", "EXPOSE 3000\n")
            run("verify.py", "scaffold-skill", tmp)
            with open(os.path.join(tmp, ".claude", "skills", "verify", "SKILL.md"), encoding="utf-8") as fh:
                skill = fh.read()
            self.assertIn("ports: 3000, 8080", skill)
            self.assertIn("docker compose -f compose.yaml up --wait", skill)


class SkillCheck(unittest.TestCase):
    EXAMPLE = os.path.join(ROOT, "examples", "verify-create")

    def test_committed_example_is_a_finished_skill(self):
        code, out, _ = run("verify.py", "skill-check", self.EXAMPLE)
        self.assertEqual(code, 0, out)

    def test_a_fresh_draft_is_not_finished(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(run("verify.py", "skill-check", tmp)[0], 1)
            write(tmp, "app.py", "")
            run("verify.py", "scaffold-skill", tmp)
            code, out, _ = run("verify.py", "skill-check", tmp, "--json")
            problems = "\n".join(json.loads(out)["problems"])
            self.assertEqual(code, 1)
            self.assertIn("TODO(verify-create)", problems)
            self.assertIn("no VERIFY.md", problems)

    def _copy(self, tmp):
        dst = os.path.join(tmp, "ex")
        shutil.copytree(self.EXAMPLE, dst, ignore=shutil.ignore_patterns(".verify-*", "__pycache__"))
        return dst, os.path.join(dst, ".claude", "skills", "verify")

    def _edit(self, path, old, new):
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        self.assertIn(old, text)
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text.replace(old, new))

    def test_each_broken_contract_is_named(self):
        cases = [
            ("SKILL.md", "name: verify\n", "name: verify\ndisable-model-invocation: true\n", "disable-model-invocation"),
            ("SKILL.md", "name: verify\n", "name: notes-verify\n", "name must be `verify`"),
            ("SKILL.md", "## Doctor", "## Health", "missing `## Doctor`"),
            ("features/create-note.md", "verify-section: Create note", "", "no `verify-section:`"),
            ("features/create-note.md", "verify-section: Create note", "verify-section: Nope", "not a VERIFY.md feature"),
            ("features/create-note.md", "## Gotchas", "## Notes", "exactly these H2s"),
            ("features/README.md", "- [Reject empty note](./reject-empty-note.md)\n", "", "not listed"),
            ("../../../VERIFY.md", "- fail-signal: expected 400 and an unchanged store for an empty title\n", "",
             "`Reject empty note` has no literal fail-signal"),
        ]
        for rel, old, new, want in cases:
            with tempfile.TemporaryDirectory() as tmp:
                repo, base = self._copy(tmp)
                self._edit(os.path.join(base, *rel.split("/")), old, new)
                code, out, _ = run("verify.py", "skill-check", repo)
                self.assertEqual(code, 1, (rel, out))
                self.assertIn(want, out, rel)

    def test_helper_must_be_executable_and_shown(self):
        if os.name == "nt":
            self.skipTest("POSIX execute bit")
        with tempfile.TemporaryDirectory() as tmp:
            repo, base = self._copy(tmp)
            helper = os.path.join(base, "scripts", "notesctl.py")
            os.chmod(helper, stat.S_IRUSR | stat.S_IWUSR)
            write(base, "scripts/extra.sh", "#!/bin/sh\n")
            os.chmod(os.path.join(base, "scripts", "extra.sh"), 0o755)
            out = run("verify.py", "skill-check", repo)[1]
            self.assertIn("notesctl.py is not executable", out)
            self.assertIn("extra.sh has no invocation shown", out)


if __name__ == "__main__":
    unittest.main()
