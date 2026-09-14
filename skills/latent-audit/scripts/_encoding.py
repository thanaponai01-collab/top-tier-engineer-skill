"""Force UTF-8 on stdout/stderr so em-dashes survive a cp1252 console."""
import sys


def utf8_streams():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8")
            except (ValueError, OSError):
                pass