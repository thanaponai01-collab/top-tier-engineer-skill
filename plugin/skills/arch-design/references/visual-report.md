# The visual report

For an owner who feels the problem but can't read the code. The page has to make them think
"oh, that's why it's slow" without opening a file.

## Where it goes

One self-contained `.html` file. When the host can publish a page (an Artifact tool), publish it.
Otherwise write `<temp dir>/architecture-review-<timestamp>.html` (`$TMPDIR`, `%TEMP%` on Windows,
else `/tmp`) and give the absolute path. Open it (`start`, `open` or `xdg-open`) from inside the
temp dir (`cd "<temp dir>" && start "" <file>`), never from the repo: on Windows the opener can
leave cache folders in the current directory. A review changes nothing in the repo. The same story and diagrams also go in the chat answer as
Mermaid, so a reader who never opens the page still gets it.

Load Mermaid from a pinned CDN version (`https://cdn.jsdelivr.net/npm/mermaid@11.4.1/dist/mermaid.min.js`)
and keep everything else inline CSS. It must read in light and dark mode, and at phone width.

## Layout, top to bottom

1. **Verdict**: one sentence in the owner's words, tied to what they feel. "Checkout waits for the
   email server, which is why it's slow and why some customers are charged but see an error."
2. **Map check**: if the project's map disagrees with the code, a callout saying where, before
   anything else.
3. **One card per candidate**, best first:
   - title in plain words and a badge: Strong / Worth exploring / Speculative
   - *What you feel*: the symptom
   - *Why it happens*: the chain, one short paragraph
   - *Before* and *After* diagrams side by side (stacked on narrow screens). Mark the bottleneck or
     the ripple in the Before picture with a red outline or a dashed "waits here" edge.
   - *What gets better*: counted ("checkout no longer waits up to 100 s"; "a new field: 6 files → 2")
   - *Risk*: two-way (easy to undo) or one-way (data, public API), in a line
   - a collapsed *Details for engineers* block: `file:line`, steps, proof command
4. **Start here**: which candidate you'd do first and why, then the question: which one to explore.

## Pictures that explain

- One idea per picture, about eight boxes at most. Split a bigger flow.
- Boxes are things the owner recognises ("Charge card", "Send receipt"), not function names.
- Draw time left to right for a flow; draw who-depends-on-whom top to bottom.
- Show the cost on the edge: "waits up to 30 s × 3", "runs again for every item", "6 files change".
- Before and After use the same boxes in the same places, so the eye sees only what moved.
- A ripple picture works for change cost: one box for the change, arrows to every file it forces.
