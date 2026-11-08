The repo in `fixture/` (it is the repo root) is a small print-shop app. Find all of the implicit
state machines in it: the states each thing can be in, how it moves between them, and where the
code does that. Tell me in plain words which of them have bugs (a state that can be reached but
should be impossible, a state nothing can leave, a move that should be refused but is not, a check
for a state that nothing ever sets). Fix the bugs you are sure of without breaking anything else,
and tell me what you fixed and what you left alone.
