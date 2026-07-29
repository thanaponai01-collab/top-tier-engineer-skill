#!/usr/bin/env python3
"""
protocol_vintage — one owner for PROTOCOL §11's rule-vintage mechanism.

WHY THIS EXISTS
---------------
§11 ends with a rule that is deliberately *general*:

    "A rule may not condemn an artifact written before it existed... A transcript
     therefore declares the rules it was written under, `PROTOCOL: <version>`, on its
     own line; any check younger than that declaration is skipped for that file...
     every check added after this one inherits the mechanism rather than re-arguing
     its own history."

"Inherits" is the load-bearing word, and it was not true: `verdict-lint.py` implemented
the mechanism privately while `run-trace.py` had no notion of it at all, so run-trace
enforced the §1 pin rule (added 1.13.0) against transcripts that declare `PROTOCOL:
1.12.0` and say in the same line that they are linted by the rules they were written
under. The grandfathering clause existed, the artifacts used it correctly, and the tool
overrode them.

This module is the mechanism, extracted so there is exactly one of it (Law 1, every rule
lives in exactly one place). A new dated check adds one constant to VINTAGE below and
one `skips()` call at its site — it never re-implements the parse, and never re-argues
its own history.

RELATIONSHIP TO THE CHECKS THEMSELVES
-------------------------------------
This module owns *when a check applies*, never *what the check decides*. The checks stay
in their tools. Grandfathering is a scope question, not a verdict.

USAGE

    import protocol_vintage as vintage
    if vintage.skips(text, vintage.PIN_RULE):
        ...   # this artifact predates the pin rule; the check does not run

TESTED BY `tools/test_tools.py`.
"""

import re

# A transcript states which PROTOCOL version judged it. Tolerant of markdown decoration
# (bold, blockquote, list item) exactly as the verdict-line parsers are, because these
# declarations are written inside reports, not machine files.
PROTOCOL_DECL_RE = re.compile(
    r'^[\s`*>#|+-]*\*{0,2}PROTOCOL\*{0,2}\s*:\s*v?(\d+)\.(\d+)', re.M)

# ---------------------------------------------------------------------------
# The vintage registry: the PROTOCOL version each dated check was introduced in.
# A check absent from this registry is undated and applies to every artifact —
# which is correct for checks that predate the mechanism itself (§5 verdict form,
# §4 ordering), because no artifact could have been written before them.
# ---------------------------------------------------------------------------
PIN_RULE = (1, 13)     # §1 subject pin  — `SUBJECT: <name> @ <revision>` (1.13.0)
SENSE_FLOOR = (1, 16)  # §11 DELIVERY block — ASKED/DID/SO/COST (1.16.0)


def declared(text):
    """The PROTOCOL version this artifact declares, as (major, minor), or None.

    None means "no declaration" — and §11 is explicit that such an artifact "is judged
    by the current rules". Absence is not grandfathering; a writer who wants the older
    rules must say so.
    """
    m = PROTOCOL_DECL_RE.search(text)
    return (int(m.group(1)), int(m.group(2))) if m else None


def skips(text, since):
    """True when `text` declares a vintage older than the check introduced at `since`.

    The asymmetry is intentional and matches §11: an undeclared artifact is judged by
    today's rules (returns False), so the mechanism can never be used to silence a check
    by simply omitting a line.
    """
    d = declared(text)
    return d is not None and d < since


def explain(since):
    """One line a non-coder can read, for a report that skipped a check."""
    return (f"skipped: this artifact declares a PROTOCOL vintage older than "
            f"{since[0]}.{since[1]}.0, when this check was introduced (PROTOCOL §11, "
            f"rule vintage — a rule may not condemn an artifact written before it existed)")
