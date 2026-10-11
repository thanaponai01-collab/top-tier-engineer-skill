I couldn't file anything. fixture/ is a git repo with no GitHub remote, and the gh CLI has no logged-in
account, so there's no tracker to post to. I did not create a repo or add a remote, since that's your
call.

What I prepared instead, in issues/: one body per move, each starting with the shared context from
the top of the audit (TAX_V2 flag, auth model untouched, the finance review it came from), then the
move copied as written.

M3 is not ready to be an issue. It has no proof line, and "tidy up the old helpers" doesn't say what
done looks like. I left it out and would ask finance or the author what should change in
utils/num.py and how to check it.

Order when filing: M1, then M2 (blocked by M1), then M4 (blocked by M2).
