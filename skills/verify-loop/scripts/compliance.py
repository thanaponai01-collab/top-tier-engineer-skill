#!/usr/bin/env python3
"""compliance.py — deterministic checks that output meets a schema, a privacy rule and a safety rule.

Each command exits 0 when the output complies and 1 when it does not, so it drops straight into
VERIFY.md as a check:

  ## Refund API
  - schema: `python scripts/compliance.py schema schemas/refund.json out/refund.json --strict`
  - privacy: `python scripts/compliance.py privacy out/ logs/`
  - guardrail: `python scripts/compliance.py guardrail tests/abuse.json -- python app.py --stdin`
  - repeat: `python scripts/compliance.py repeat 3 -- python app.py --demo`

  schema     Validate a JSON file (or - for stdin) against a JSON Schema. A keyword this script does
             not implement is an ERROR (exit 2), never a silent pass. --strict also treats an object
             with no `additionalProperties` as closed, so an extra field fails.
  privacy    Scan files or folders for emails, card numbers (Luhn), national IDs, cloud keys, tokens
             and private keys. Prints where and what kind, never the value. --allow REGEX skips a match.
  guardrail  Run a command once per abuse case (a JSON list of {name, stdin, must_match,
             must_not_match, exit}) and check what it printed. A case list that is empty is an error.
  repeat     Run a command N times; the output must be byte-identical every time.

Stdlib only. Exit: 0 complies, 1 does not, 2 the check itself could not run.
"""
import argparse, json, os, re, subprocess, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _encoding import utf8_streams

SKIP_DIRS = {".git", "node_modules", "venv", ".venv", "__pycache__", "dist", "build", "target", ".tox"}


# ---- schema -------------------------------------------------------------------------------

KNOWN = {"$schema", "$id", "$ref", "$defs", "definitions", "title", "description", "default", "examples",
         "$comment", "type", "enum", "const", "properties", "required", "additionalProperties", "items",
         "minItems", "maxItems", "uniqueItems", "minLength", "maxLength", "pattern", "minimum", "maximum",
         "exclusiveMinimum", "exclusiveMaximum", "allOf", "anyOf", "oneOf", "not", "format"}
TYPES = {"string": str, "boolean": bool, "array": list, "object": dict, "null": type(None)}


class SchemaError(Exception):
    pass


def is_type(v, t):
    if t == "integer":
        return isinstance(v, int) and not isinstance(v, bool)
    if t == "number":
        return isinstance(v, (int, float)) and not isinstance(v, bool)
    if t not in TYPES:
        raise SchemaError(f"unknown type {t!r}")
    return isinstance(v, TYPES[t]) and not (t != "boolean" and isinstance(v, bool))


def deref(ref, root):
    if not ref.startswith("#/"):
        raise SchemaError(f"only local $ref is supported, got {ref!r}")
    node = root
    for part in ref[2:].split("/"):
        part = part.replace("~1", "/").replace("~0", "~")
        if not isinstance(node, dict) or part not in node:
            raise SchemaError(f"$ref {ref!r} does not resolve")
        node = node[part]
    return node


def validate(v, sch, root, path, strict, errs):
    if sch is True:
        return
    if sch is False:
        errs.append(f"{path}: nothing is allowed here")
        return
    if not isinstance(sch, dict):
        raise SchemaError(f"{path}: a schema must be an object, got {type(sch).__name__}")
    for k in sch:
        if k not in KNOWN:
            raise SchemaError(f"unsupported keyword {k!r}: refusing to pass what cannot be checked")
    if "$ref" in sch:
        validate(v, deref(sch["$ref"], root), root, path, strict, errs)
    if "type" in sch:
        types = sch["type"] if isinstance(sch["type"], list) else [sch["type"]]
        if not any(is_type(v, t) for t in types):
            errs.append(f"{path}: expected {'/'.join(types)}, got {type(v).__name__}")
            return
    if "enum" in sch and v not in sch["enum"]:
        errs.append(f"{path}: {v!r} is not one of {sch['enum']}")
    if "const" in sch and v != sch["const"]:
        errs.append(f"{path}: expected {sch['const']!r}, got {v!r}")
    if isinstance(v, str):
        if "minLength" in sch and len(v) < sch["minLength"]:
            errs.append(f"{path}: shorter than {sch['minLength']}")
        if "maxLength" in sch and len(v) > sch["maxLength"]:
            errs.append(f"{path}: longer than {sch['maxLength']}")
        if "pattern" in sch and not re.search(sch["pattern"], v):
            errs.append(f"{path}: does not match /{sch['pattern']}/")
    if is_type(v, "number"):
        for key, bad in (("minimum", lambda a, b: a < b), ("maximum", lambda a, b: a > b),
                         ("exclusiveMinimum", lambda a, b: a <= b), ("exclusiveMaximum", lambda a, b: a >= b)):
            if key in sch and bad(v, sch[key]):
                errs.append(f"{path}: {v} violates {key} {sch[key]}")
    if isinstance(v, list):
        if "minItems" in sch and len(v) < sch["minItems"]:
            errs.append(f"{path}: fewer than {sch['minItems']} items")
        if "maxItems" in sch and len(v) > sch["maxItems"]:
            errs.append(f"{path}: more than {sch['maxItems']} items")
        if sch.get("uniqueItems") and len({json.dumps(x, sort_keys=True) for x in v}) != len(v):
            errs.append(f"{path}: items are not unique")
        if "items" in sch:
            for i, x in enumerate(v):
                validate(x, sch["items"], root, f"{path}[{i}]", strict, errs)
    if isinstance(v, dict):
        props = sch.get("properties", {})
        for r in sch.get("required", []):
            if r not in v:
                errs.append(f"{path}: missing required field {r!r}")
        for k, x in v.items():
            if k in props:
                validate(x, props[k], root, f"{path}.{k}", strict, errs)
            elif "additionalProperties" in sch:
                ap = sch["additionalProperties"]
                if ap is False:
                    errs.append(f"{path}: unexpected field {k!r}")
                elif ap is not True:
                    validate(x, ap, root, f"{path}.{k}", strict, errs)
            elif strict and ("properties" in sch or "type" in sch):
                errs.append(f"{path}: unexpected field {k!r} (--strict: an unlisted field is a failure)")
    for sub in sch.get("allOf", []):
        validate(v, sub, root, path, strict, errs)
    if "anyOf" in sch and not any(_ok(v, s, root, path, strict) for s in sch["anyOf"]):
        errs.append(f"{path}: matches none of anyOf")
    if "oneOf" in sch:
        n = sum(_ok(v, s, root, path, strict) for s in sch["oneOf"])
        if n != 1:
            errs.append(f"{path}: matches {n} of oneOf, needs exactly 1")
    if "not" in sch and _ok(v, sch["not"], root, path, strict):
        errs.append(f"{path}: matches a schema it must not")


def _ok(v, sch, root, path, strict):
    e = []
    validate(v, sch, root, path, strict, e)
    return not e


def cmd_schema(schema_path, data_path, strict):
    try:
        with open(schema_path, encoding="utf-8") as fh:
            sch = json.load(fh)
        raw = sys.stdin.read() if data_path == "-" else open(data_path, encoding="utf-8").read()
        data = json.loads(raw)
    except (OSError, ValueError) as e:
        print(f"ERROR  cannot read schema or data: {e}")
        return 2
    errs = []
    try:
        validate(data, sch, sch, "$", strict, errs)
    except SchemaError as e:
        print(f"ERROR  {e}")
        return 2
    for e in errs:
        print(f"FAIL  {e}")
    print(f"schema: {'complies' if not errs else f'{len(errs)} violation(s)'} ({data_path} vs {schema_path})")
    return 1 if errs else 0


# ---- privacy ------------------------------------------------------------------------------

def thai_id(digits):
    if len(digits) != 13 or digits[0] == "0":
        return False
    return (11 - sum(int(digits[i]) * (13 - i) for i in range(12)) % 11) % 10 == int(digits[12])


def luhn(digits):
    d = [int(c) for c in digits][::-1]
    total = sum(d[0::2]) + sum(sum(divmod(x * 2, 10)) for x in d[1::2])
    return 13 <= len(d) <= 19 and total % 10 == 0


PII = [
    ("email", re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"), None),
    ("card number", re.compile(r"\b(?:\d[ -]?){13,19}\b"), lambda m: luhn(re.sub(r"\D", "", m))),
    ("national id (TH)", re.compile(r"\b\d{1}[ -]?\d{4}[ -]?\d{5}[ -]?\d{2}[ -]?\d\b"), lambda m: thai_id(re.sub(r"\D", "", m))),
    ("aws access key", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"), None),
    ("private key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), None),
    ("token", re.compile(r"\b(?:sk-[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{30,}|xox[abp]-[A-Za-z0-9-]{10,})\b"), None),
    ("secret assignment", re.compile(r"(?i)\b(?:api[_-]?key|secret|password|passwd|token)\b\s*[:=]\s*['\"]?[^\s'\"]{8,}"), None),
]


def scan_files(paths):
    for p in paths:
        if os.path.isdir(p):
            for root, dirs, files in os.walk(p):
                dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
                for f in sorted(files):
                    yield os.path.join(root, f)
        else:
            yield p


def cmd_privacy(paths, allow):
    allow_re = [re.compile(a) for a in allow]
    hits, scanned = [], 0
    for f in scan_files(paths):
        try:
            with open(f, encoding="utf-8", errors="strict") as fh:
                lines = fh.read().splitlines()
        except (OSError, UnicodeDecodeError):
            continue  # unreadable or binary: not scannable, and said so below
        scanned += 1
        for n, line in enumerate(lines, 1):
            for kind, rx, ok in PII:
                for m in rx.finditer(line):
                    if ok and not ok(m.group(0)):
                        continue
                    if any(a.search(m.group(0)) for a in allow_re):
                        continue
                    hits.append((f, n, kind))
    if not scanned:
        print("ERROR  no readable text file to scan: a scan of nothing proves nothing")
        return 2
    for f, n, kind in hits:
        print(f"FAIL  {f}:{n}  {kind}")
    print(f"privacy: {len(hits)} hit(s) in {scanned} file(s) (values are never printed)")
    return 1 if hits else 0


# ---- guardrail and repeat -----------------------------------------------------------------

def run_cmd(cmd, stdin=None, timeout=60):
    try:
        p = subprocess.run(cmd, input=stdin, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=timeout)
    except (OSError, subprocess.SubprocessError) as e:
        return None, f"{type(e).__name__}: {e}"
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def cmd_guardrail(cases_path, cmd, timeout):
    try:
        with open(cases_path, encoding="utf-8") as fh:
            cases = json.load(fh)
    except (OSError, ValueError) as e:
        print(f"ERROR  cannot read cases: {e}")
        return 2
    if not isinstance(cases, list) or not cases:
        print("ERROR  no abuse cases: a guardrail with nothing to attack is not tested")
        return 2
    if not cmd:
        print("ERROR  no command after --")
        return 2
    bad = 0
    for i, c in enumerate(cases):
        name = c.get("name", f"case {i + 1}")
        code, out = run_cmd(cmd, c.get("stdin", ""), timeout)
        why = []
        if code is None:
            why.append(f"could not run: {out}")
        else:
            for rx in c.get("must_match", []):
                if not re.search(rx, out):
                    why.append(f"output lacks /{rx}/")
            for rx in c.get("must_not_match", []):
                if re.search(rx, out):
                    why.append(f"output contains /{rx}/")
            want = c.get("exit")
            if want == "nonzero" and code == 0:
                why.append("exited 0, expected a refusal")
            elif isinstance(want, int) and code != want:
                why.append(f"exit {code}, expected {want}")
        print(f"{'FAIL' if why else 'PASS'}  {name}" + (f"  ({'; '.join(why)})" if why else ""))
        bad += bool(why)
    print(f"guardrail: {len(cases) - bad}/{len(cases)} cases hold")
    return 1 if bad else 0


def cmd_repeat(n, cmd, timeout):
    if not cmd or n < 2:
        print("ERROR  repeat needs N >= 2 and a command after --")
        return 2
    first = None
    for i in range(n):
        code, out = run_cmd(cmd, None, timeout)
        if code is None:
            print(f"ERROR  {out}")
            return 2
        if first is None:
            first = (code, out)
        elif (code, out) != first:
            print(f"FAIL  run {i + 1} differs from run 1 (exit {code} vs {first[0]})")
            a, b = first[1].splitlines(), out.splitlines()
            for j in range(max(len(a), len(b))):
                if (a[j] if j < len(a) else None) != (b[j] if j < len(b) else None):
                    print(f"      line {j + 1}: {a[j] if j < len(a) else '<missing>'!r} vs {b[j] if j < len(b) else '<missing>'!r}")
                    break
            return 1
    print(f"repeat: {n} runs, identical output")
    return 0


def split_dashdash(argv):
    return (argv[:argv.index("--")], argv[argv.index("--") + 1:]) if "--" in argv else (argv, [])


def main():
    utf8_streams()
    argv, cmd = split_dashdash(sys.argv[1:])
    ap = argparse.ArgumentParser(description="Schema, privacy and guardrail checks that exit 0 or 1.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("schema")
    s.add_argument("schema")
    s.add_argument("data", help="JSON file, or - for stdin")
    s.add_argument("--strict", action="store_true", help="an unlisted field in an object fails")
    p = sub.add_parser("privacy")
    p.add_argument("paths", nargs="+")
    p.add_argument("--allow", action="append", default=[], help="regex of a match to accept (repeatable)")
    g = sub.add_parser("guardrail")
    g.add_argument("cases")
    g.add_argument("--timeout", type=int, default=60)
    r = sub.add_parser("repeat")
    r.add_argument("n", type=int)
    r.add_argument("--timeout", type=int, default=60)
    a = ap.parse_args(argv)
    if a.cmd == "schema":
        sys.exit(cmd_schema(a.schema, a.data, a.strict))
    if a.cmd == "privacy":
        sys.exit(cmd_privacy(a.paths, a.allow))
    if a.cmd == "guardrail":
        sys.exit(cmd_guardrail(a.cases, cmd, a.timeout))
    sys.exit(cmd_repeat(a.n, cmd, a.timeout))


if __name__ == "__main__":
    main()
