## What can go: nothing is proven safe to delete yet, but two modules are strong candidates

I swept all 12 modules in `fixture/` (one file per module; ARCHITECTURE.md is the only other file). The dead-code finder flagged two modules and four functions as possibly dead. I ran the app's code to check which modules actually load. Two modules really are unused by everything in this folder.

I can't move them to the delete list because one of the three required checks can't be finished from here: making sure nothing outside the repo uses them. There is no git history, CI config, cron file or deployment config to look at, so a scheduled job, another service or someone running a script could still call them and I'd have no way to see it. Only someone who knows how this code is deployed can close that check.

| Candidate | Status | Proof / unfinished check | Proposed action |
|---|---|---|---|
| `app/services/legacy_export.py` (`to_xml`) | **Watch: strongest delete candidate** | 1. Search: no import, no text match, not in `ENABLED_PLUGINS`. 2. Outside callers: **not checked**. 3. Test run: I called `handle()` and `registry.load()`, and this module never loaded. Its docstring says it was "superseded by the plugins". | Confirm nothing outside the repo calls `to_xml`, then delete it in one commit. |
| `app/models/notify.py` (`subject`) | **Watch, and a layer breach** | 1. Search: no references. 2. Outside callers: **not checked**. 3. Test run: it never loaded. | Same confirmation, then delete. Deleting it also removes the codebase's only layer breach. |
| `app/plugins/csv_out.py` (`render`) | **Keep: it is used** | Flagged only because nothing imports it directly. `registry.py:4` names it as a string in `ENABLED_PLUGINS`, and `registry.load()` loads it with `importlib`. I ran it: `render([1,2])` returns `"1\n2"`. | Keep. ARCHITECTURE.md:9 says plugins are loaded this way. |
| `app/routes/web.py` `handle` | **Keep: likely entry point** | Nothing in the folder calls it, but it's the interface layer's HTTP handler, and it is the only way into `services/orders` and `models/order`. | Keep. |
| `app/registry.py` `load` | **Keep: likely entry point** | Nothing in the folder calls it either. It is the only thing that loads the plugins. | Keep. |

**Deleting both watch items gets you:** two files gone (about 11 lines), the leftover XML exporter retired, and the layer breach below gone with no other code change.

**An open question about entry points:** nothing in the folder calls `handle()` or `registry.load()`, and there's no `main`, server setup or route table. So whatever starts this app lives outside `fixture/`. That's another reason to confirm the outside-callers check before deleting anything.

## Layer check

I took the layer order from `ARCHITECTURE.md:3-7`: routes (interface), then services (domain), then models (data). A module may only import its own layer or a lower one.

- **One breach:** `app/models/notify.py:2` has `from app.routes.web import BANNER`. A data module reaches up into the interface layer just to get the string `"orders"`. There are two fixes. You can change the code: move `BANNER` down to models or a shared constants module, or delete `notify.py` as above. Or you can change the declaration to allow it, which isn't recommended. Since `notify.py` appears unused, deleting it is the simplest.
- `app/plugins/` and `app/registry.py` aren't in any declared layer, so they weren't checked. That's a gap in the declaration, not a clean result.

## Problems I noticed but didn't chase

- `app/models/order.py:2`: `ROWS` is a list shared by the whole process that only ever grows. Every order since startup stays in memory, and requests running at the same time all share it.
- `app/routes/web.py:8` and `app/services/orders.py:6`: a request missing `items` or `price` raises an error (`KeyError`) that nothing handles, so the HTTP layer surfaces it as a generic failure.

## Raw output

```
LAYER BREACHES (proven) — declared order: interface > domain > data
  fixture\app\models\notify.py:2  app.models.notify (data) -> app.routes.web (interface)
  note: 4 modules match no declared layer: app.__init__, app.plugins.__init__, app.plugins.csv_out, app.registry
DEAD MODULE CANDIDATES (suspected): app.models.notify, app.services.legacy_export
UNUSED DEFS (suspected): handle (web.py:7), render (csv_out.py:4), subject (notify.py:5), to_xml (legacy_export.py:4)
LATENT: findings(dead: 2, unused: 4, layer-breaches: 1)
```

Test run, calling `handle()` and `registry.load()`. These are all the app modules that loaded; `legacy_export` and `notify` are not among them:
`app, app.models, app.models.order, app.plugins, app.plugins.csv_out, app.registry, app.routes, app.routes.web, app.services, app.services.orders`

This was a report only; nothing in `fixture/` was changed. The layers file I wrote for the check is in `../la-scratch/layers.txt`, outside the repo. Once the outside-callers question is settled, I can delete the two candidates, one per commit with the proof in each commit message, so either one can be undone on its own.