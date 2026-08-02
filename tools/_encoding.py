"""_encoding — force UTF-8 on stdout/stderr so § and em-dashes survive a cp1252 console.

Shared by every tools/*.py that prints to a director's terminal or CI log (DEBT_LEDGER
D-5, repaid): each tool still imports this rather than opening a socket back to the
suite, so the standalone-copy guarantee for tools/ now covers "vendor two files," not
zero.
"""
import sys


def utf8_streams():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8")
            except (ValueError, OSError):
                pass
