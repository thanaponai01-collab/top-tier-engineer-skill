#!/usr/bin/env python3
"""
spec_check.py — refuse a brief that does not fill work/SPEC_TEMPLATE.md.

    python tools/spec_check.py BRIEF.md [work/briefs/<skill>.md ...]

The brief is plain prose under six headings. Each term is marked by an HTML comment, such as
`<!-- end state -->`, put in front of the prose that covers it; the marker is hidden when the brief
is rendered, so the wording is free. Exit 0 when every file passes, 1 with every problem listed
otherwise.
"""
import os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SECTIONS = [("Intent", ["purpose", "end state", "done when"]),
            ("Context", ["grounding", "scope", "non-goals"]),
            ("Guardrails", ["constraints", "invariants", "escalation"]),
            ("Freedom", ["latitude"]),
            ("Gates", ["precondition", "postcondition", "evidence"]),
            ("Output", ["deliverable", "acceptance", "verification"])]
SLOT = re.compile(r"\[\[fill:")
MARKER = re.compile(r"<!--\s*(.*?)\s*-->", re.S)
EVIDENCE = re.compile(r"`[^`]+`|[\w./-]+\.(?:md|py|txt|json|log)\b")


def split_sections(text):
    """{name: body} for each `## Name` heading (an `N.` before the name is allowed), in order."""
    found, order, cur = {}, [], None
    for line in text.splitlines():
        m = re.match(r"##\s+(?:\d+\.\s*)?(.+?)\s*$", line)
        if m and not line.startswith("###"):
            cur = m.group(1)
            order.append(cur)
            found[cur] = []
        elif cur is not None:
            found[cur].append(line)
    return {k: "\n".join(v) for k, v in found.items()}, order


def marked(body):
    """[(marker, the prose after it up to the next marker)] for one part."""
    parts = MARKER.split(body)
    return [(parts[i].lower(), " ".join(parts[i + 1].split())) for i in range(1, len(parts), 2)]


def check(path):
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    except OSError as e:
        return ["cannot read: %s" % e]
    problems = []
    first = text.find("\n## ")
    head = text if first < 0 else text[:first]
    text = MARKER.sub("", head) + ("" if first < 0 else text[first:])  # the header comment is help
    slots = SLOT.findall(re.sub(r"`[^`\n]*`", "", MARKER.sub("", text)))  # a slot quoted as code is prose
    if slots:
        problems.append("unfilled [[fill: ...]] slot: %d left" % len(slots))
    sections, order = split_sections(text)
    wanted = [name for name, _ in SECTIONS]
    present = [n for n in order if n in wanted]
    if present != [n for n in wanted if n in present]:
        problems.append("parts out of order: %s (want %s)"
                        % (", ".join(present), ", ".join(wanted)))
    for name, terms in SECTIONS:
        if name not in sections:
            problems.append("missing part: ## %s" % name)
            continue
        found = marked(sections[name])
        names = [m for m, _ in found]
        for m in names:
            if m not in terms:
                problems.append("%s: unknown marker <!-- %s --> (this part takes %s)"
                                % (name, m, ", ".join(terms)))
        for term in terms:
            if term not in names:
                problems.append("%s: nothing covers the %s (put <!-- %s --> before the prose "
                                "that does)" % (name, term, term))
        for m, prose in found:
            if m in terms and not prose:
                problems.append("%s: <!-- %s --> has no prose after it" % (name, m))
        if name == "Gates":
            counts = {t: names.count(t) for t in terms}
            if len(set(counts.values())) > 1:
                problems.append("Gates: each stage needs all three markers (have %s)"
                                % ", ".join("%d %s" % (counts[t], t) for t in terms))
            for m, prose in found:
                if m == "evidence" and prose and not EVIDENCE.search(prose):
                    problems.append("Gates: evidence '%s' names no `command` or file" % prose[:50])
        if name == "Output":
            for m, prose in found:
                if m == "verification" and prose and not re.search(r"`[^`]+`", prose):
                    problems.append("Output: verification names no `command`")
            out = MARKER.sub("", sections[name])
            named = sorted(set(re.findall(r"tests/[\w/.-]+\.py", out)))
            if not named:
                problems.append("Output: acceptance names no tests/*.py that holds it")
            for test in named:
                if not os.path.exists(os.path.join(ROOT, test)):
                    problems.append("Output: %s does not exist" % test)
    return problems


def main(argv):
    if not argv:
        print(__doc__.strip())
        return 2
    bad = 0
    for path in argv:
        problems = check(path)
        if problems:
            bad += 1
            print("SPEC REFUSED %s" % path)
            for p in problems:
                print("  - %s" % p)
        else:
            print("SPEC OK %s" % path)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
