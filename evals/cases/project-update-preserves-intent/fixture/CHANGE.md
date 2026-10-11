# Completed task
Login now retains the return URL through the shared redirect helper. No checks ran.
Session expiry is unfinished. Reconcile the supplied before/after change in src/shared/redirect.py
and the current callers; source files are the completed product, not edits to make here.
Before: preserve(target) returned '/'. After: preserve(target) returns target.
