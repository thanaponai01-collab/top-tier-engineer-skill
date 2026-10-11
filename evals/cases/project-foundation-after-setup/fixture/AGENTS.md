# Project instructions

MANUAL: Keep amounts in integer cents.
This is a Python library. Run `python -m unittest discover tests` from this folder.
No CI or deployment setup requested. Preserve product behavior and the live gateway note.

<!-- agent-routing -->
Coordinator: the current session model.
Execution: plugin agent drive-executor (Sonnet) for bounded implementation and local checks.
Discovery: plugin agent setup-reader (Haiku) for bounded read-only evidence collection.
Workers receive assigned paths, acceptance checks, allowed edits and limits.
<!-- /agent-routing -->
