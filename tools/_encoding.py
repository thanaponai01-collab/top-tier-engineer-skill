"""Force UTF-8 on stdout/stderr so § and em-dashes survive a cp1252 console.

Shared by every tools/*.py that prints to a terminal. Copying a tool out of this
suite means vendoring this file with it.
"""
import sys


def utf8_streams():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8")
            except (ValueError, OSError):
                pass
