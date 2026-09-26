---
name: feature-map
description: Map what a system has and how a user reaches each feature (route, click target, shortcut, CLI command), in a FEATURES.md the next session reads instead of rediscovering. Use to learn an unfamiliar app, before driving or testing one, when an agent asks "what can this do / how do I get to X", or to keep that map from going stale. Web, CLI and desktop apps.
---

# Feature Map

An agent that does not know what a system has re-explores it every session, and drives it by
guessing. A feature map is the memory: what features exist, what each does, and the exact way in.
It earns trust only if it can be wrong loudly, so every entry point in it is something a script
can check against the code, and every feature says how it is known.

## What goes in a feature

One `##` section per feature in `FEATURES.md` at the repo root. Each bullet is `key: value`:

```
## Checkout
- what: Pay for the cart and get an order id.
- route: `/checkout` @ src/routes.tsx
- click: `[data-testid=pay-btn]` @ src/Cart.tsx
- shortcut: `Ctrl+Enter` @ src/keys.ts :: submitOrder
- cli: `shop checkout` @ cli.py
- trace: `checkout` @ src/routes.tsx > `placeOrder` @ src/orders.ts > `orders` @ db/schema.sql
- verify: Checkout
- status: proven @ 3f2a1bc: drove /checkout in a browser, order id shown
```

- **what:** what it does for its user, in one sentence, not what the code is called.
- **Entry points** (`route`, `click`, `shortcut`, `cli`, `menu`; `api` reads as `route`): every way in,
  as `` `anchor` @ file :: needle ``. `check` looks for the needle in that file. It is derived from the
  anchor (the selector's value, the route's path, the last key, the subcommand); write `:: needle`
  when that is not what the code contains. Prefer a stable anchor (a test-id attribute, an accessible
  name, an id) over a class or a position.
- **trace:** the path from entry point to effect, steps joined by ` > `, each `` `symbol` @ file ``
  (handler, then what it calls, then the row, file or request that changes). Each step must be in its
  file and referenced from the step before it, so an agent can follow the feature without searching.
- **verify:** the VERIFY.md section that proves it (`verify-loop`). No section, no proof it works.
- **status:** an evidence label, then how you know it. Pin it to the commit you ran it at
  (`proven @ <short sha>`): `check` then flags it as drifted once a file of that feature changes.
- Also worth a line when true: **needs** (login, a flag, a role, seeded data) and **effect** (what
  changes: a row, a file, a request).

*Evidence labels: **proven** = you ran it · **traced** = you read the whole chain, start to
end · **suspected** = neither.*

*Test:* an agent that has read only this file could open the feature, with no searching.

## Build it

1. **Draft from the code.** `python <this skill's base directory>/scripts/features.py init` lists
   the entry points it finds (server routes, page files, test-id attributes and button ids, accelerators
   and hotkeys, CLI subcommands) grouped by likely feature. It is a scan, not the map: it cannot see
   a click path built at runtime or a shortcut set in config.
2. **Trace each feature.** Follow it from the entry point to its effect and write the `trace:` path, reading
   every hop rather than guessing the middle. A hop you cannot follow is a finding, and the path stops there.
3. **Read the code behind each group and regroup by real feature.** Trace from where the system
   starts (router, menu template, CLI dispatcher). Add what the scan could not see. Where the map
   would need a guess, write `suspected` rather than a confident line.
4. **Prove the entry points by running them.** Web: open the page, use the click path, screenshot.
   CLI: run the command with `--help`, then once for real. Desktop: press the shortcut, open the
   menu item. Set `proven` only for what you ran; a route you read but did not hit is `traced`.
   A dead entry point found here is a finding for `wire-check`, not a line to keep.
5. **Link each feature to VERIFY.md** (`verify-loop`): name its section, or add one. A feature with
   no check is listed as a gap, not hidden.
6. **Check the map.** `python <base>/scripts/features.py check --strict` must exit 0.

*Test:* `check --strict` prints `0 stale | 0 broken | 0 untraced | 0 unmapped | 0 unlinked | 0 unlabeled | 0 undescribed | 0 drifted`.

## What `check` says

- **STALE**: a mapped entry point or trace step the code no longer has (renamed selector, moved route, deleted
  file). Fix the map or the code, whichever is wrong; never delete the line to make it green
  without finding out which.
- **BROKEN**: a trace step that exists but is not referenced from the step before it, so the path is
  no longer a real call chain (a renamed callee, a call removed). Re-trace that hop.
- **Untraced**: a feature with no `trace:` path.
- **Unmapped**: the code declares an entry point the map lacks: a feature nobody wrote down.
- **Unlinked, unlabeled, undescribed**: a feature with no VERIFY.md section, no status, or no `what`.
  Also lists VERIFY.md sections no feature links.
- **Drifted**: a status pinned `@ commit` whose feature has files changed since (or a commit git cannot
  resolve). Re-run the entry points, then re-pin; never re-pin without re-running.
- `--strict` fails on the last five groups too; without it only STALE and BROKEN fail. Use `--strict` for
  "done".

`check` reads code text, so it proves an entry point and each trace hop are *declared and linked*, not
that they *work*. Step 3 is
what makes an entry `proven`; the script keeps that claim honest afterwards, when the code moves.

## After a change

`python <base>/scripts/features.py impact` lists the features whose entry or trace files changed
(git diff against HEAD, plus untracked; `--base REF` or `--files a b` to choose) and the VERIFY.md
section to rerun for each. Changed code no feature names is a gap in the map, or shared code to
check by hand. Run those sections with `verify-loop`, then re-pin what you re-proved.

## Using the map

Read `FEATURES.md` first when asked to drive, test, document or change an app, and take the entry
point from it rather than searching. If an entry in it fails when you use it, fix the map in the
same change. After any change that adds, renames or removes a route, control, shortcut or command,
run `check`. It is the drift alarm.

## Rules

- **The map records the running system.** A feature you expect the system to have, or one on the
  roadmap, does not go in. Say so in a `## Not built` section if it helps.
- **Never invent an entry point.** An anchor you did not see in the code or on screen is wrong until
  shown otherwise.
- **Keep it short.** One line per fact. A map too long to read is a map nobody opens.

Mapping every feature to its checks is `verify-loop`; a feature whose entry point exists but does
nothing is `wire-check`; a picture of the structure is `arch-map`. This skill stands without them:
without them, the file above is the whole job.
