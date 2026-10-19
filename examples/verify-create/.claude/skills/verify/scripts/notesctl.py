#!/usr/bin/env python3
"""Drive the notes service like a user would; every proof lands in .verify-evidence/.

  notesctl.py seed                 fresh .verify-data/ with one seed note
  notesctl.py ready                exit 0 once /health answers
  notesctl.py doctor               right instance? build digest and data dir must match this checkout
  notesctl.py drive create-note    POST a note, read it back over HTTP and from the store
  notesctl.py drive reject-empty   POST an empty title: 400, store unchanged
Options: --port 8765 --data .verify-data --evidence .verify-evidence (paths from the project root)
"""
import argparse, hashlib, json, os, shutil, sys, urllib.error, urllib.request

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))


def call(port, method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(f"http://127.0.0.1:{port}{path}", data=data, method=method,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status, json.loads(r.read() or b"null")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"null")


def stored(a):
    with open(os.path.join(a.data, "notes.json"), encoding="utf-8") as fh:
        return json.load(fh)


def save(a, feature, record):
    d = os.path.join(a.evidence, feature)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "run.json"), "w", encoding="utf-8") as fh:
        json.dump(record, fh, indent=2)
    print(f"evidence: {os.path.relpath(os.path.join(d, 'run.json'), ROOT)}")


def seed(a):
    shutil.rmtree(a.data, ignore_errors=True)
    os.makedirs(a.data)
    with open(os.path.join(a.data, "notes.json"), "w", encoding="utf-8") as fh:
        json.dump([{"id": 1, "title": "Grocery list", "body": ""}], fh)
    return 0


def ready(a):
    try:
        return 0 if call(a.port, "GET", "/health")[1].get("ok") else 1
    except OSError:
        return 1


def doctor(a):
    with open(os.path.join(ROOT, "app.py"), "rb") as fh:
        want = {"build": hashlib.sha256(fh.read()).hexdigest()[:16],
                "data": os.path.join(a.data, "notes.json")}
    try:
        _, got = call(a.port, "GET", "/health")
    except OSError as exc:
        print(f"DOCTOR no instance on port {a.port}: {exc}")
        return 1
    bad = [k for k in want if got.get(k) != want[k]]
    for k in bad:
        print(f"DOCTOR MISMATCH {k}: expected {want[k]}, observed {got.get(k)}")
    print(f"DOCTOR {'ok' if not bad else 'wrong instance'}: pid {got.get('pid')} build {got.get('build')}")
    return 1 if bad else 0


def create_note(a):
    before = stored(a)
    code, note = call(a.port, "POST", "/notes", {"title": "Release checklist", "body": "Tag and publish"})
    _, listed = call(a.port, "GET", "/notes")
    after = stored(a)
    save(a, "create-note", {"action": "POST /notes title=Release checklist", "status": code,
                            "response": note, "listed": listed, "store_before": before, "store_after": after})
    if code != 201:
        print(f"expected 201 from POST /notes, got {code}")
        return 1
    if not any(n["title"] == "Release checklist" for n in after):
        print(f"expected stored note 'Release checklist', got {[n['title'] for n in after]}")
        return 1
    if not any(n["title"] == "Release checklist" for n in listed):
        print(f"expected GET /notes to list 'Release checklist', got {[n['title'] for n in listed]}")
        return 1
    return 0


def reject_empty(a):
    before = stored(a)
    code, body = call(a.port, "POST", "/notes", {"title": "   "})
    after = stored(a)
    save(a, "reject-empty", {"action": "POST /notes title='   '", "status": code, "response": body,
                             "store_before": before, "store_after": after})
    if code != 400 or after != before:
        print(f"expected 400 and an unchanged store for an empty title, got {code} "
              f"and {len(after) - len(before)} new note(s)")
        return 1
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("action", choices=["seed", "ready", "doctor", "drive"])
    ap.add_argument("feature", nargs="?", choices=["create-note", "reject-empty"])
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--data", default=".verify-data")
    ap.add_argument("--evidence", default=".verify-evidence")
    a = ap.parse_args()
    a.data, a.evidence = (os.path.join(ROOT, p) for p in (a.data, a.evidence))
    if a.action == "drive":
        return {"create-note": create_note, "reject-empty": reject_empty}[a.feature or "create-note"](a)
    return {"seed": seed, "ready": ready, "doctor": doctor}[a.action](a)


if __name__ == "__main__":
    sys.exit(main())
