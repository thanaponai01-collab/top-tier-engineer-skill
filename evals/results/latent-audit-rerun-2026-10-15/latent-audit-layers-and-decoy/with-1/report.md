## Summary: nothing is cleared for deletion yet. Two modules are almost certainly dead, and one layer rule is broken.

I swept all 12 modules in `fixture/` (11 `.py` files plus `ARCHITECTURE.md`). Python runs here, so I could run the real entry points and see which modules load. One check can't be done from inside the repo: whether anything **outside** it calls this code (cron jobs, other services, people running scripts). There's no git history, CI config, cron file or deploy config in the fixture to check against. Under the skill's rules, any unfinished check keeps a candidate on **watch** instead of the delete list.

**What can go, once you confirm nothing outside calls it:**

| Candidate | Status | Proof | Unfinished | Proposed action |
|---|---|---|---|---|
| `app/services/legacy_export.py` (`to_xml`) | **watch**: strongest delete candidate | Search: no import, string, config or dynamic reference anywhere in the tree. Tracer: never loaded when `handle()` and `registry.load()` run. Its own docstring says it was "superseded by the plugins". | Outside callers (e.g. someone running an XML export by hand, another service) | Delete in its own commit once the owner confirms no outside caller |
| `app/models/notify.py` (`subject`) | **watch**, and it's also the layer breach | Search: no reference anywhere. Tracer: never loaded. It works if imported directly (`subject(7)` returns `"orders #7"`), so it isn't broken, just unused. | Outside callers (e.g. an email or notification worker in another repo) | Delete in its own commit once confirmed. Deleting it also removes the only layer breach. |

**Keep these. They look dead to the script but aren't:**

| Candidate | Status | Why it stays |
|---|---|---|
| `app/plugins/csv_out.py` (`render`) | **live** | No `import` statement mentions it, but `app/registry.py:4` names it as a string in `ENABLED_PLUGINS`, and `registry.load()` loads it at `registry.py:8`. The tracer confirmed it loads and `render([1,2])` returns `'1\n2'`. `ARCHITECTURE.md:9-10` says plugins are resolved this way on purpose. Deleting it would be the exact mistake this audit exists to prevent. |
| `app/routes/web.py: handle` | **live (entry point)** | Nothing in the repo calls it because it's the HTTP handler, called from outside. The tracer confirmed it works: `handle(...)` places an order and returns `1`. |

**Layer breach:** I checked against the declaration at `ARCHITECTURE.md:3-7` ("A module may import its own layer or a lower one, never a higher one"; the order is routes > services > models).

- `app/models/notify.py:2`: `from app.routes.web import BANNER`. A data-layer module reaches up into the interface layer just to get the string `"orders"`. That ties the data layer to the HTTP module and everything it imports (`services.orders` and `models.order`). It doesn't cause a circular import today, but it would the moment `models/order.py` imported `notify`. There are two ways to fix it, and which one is your call:
  1. **Fix the code:** move `BANNER` down into `app/models/` (or into a shared constants module), or delete `notify.py` if it really is dead.
  2. **Change the declaration:** update `ARCHITECTURE.md` to allow this import. I don't recommend it, because a data layer that depends on the HTTP layer defeats the point of having layers.
- `app/plugins/` and `app/registry.py` don't belong to any declared layer. `ARCHITECTURE.md` describes them, but not where they sit in the layer order. That's an unchecked area, not a clean one.

**What deleting both candidates buys:** two files (about 11 lines), the only layer breach, and one misleading "old XML export" that the next person won't have to wonder about. It's a small win; the repo is already lean.

### Script output and checks run
- **Script:** `graph-audit.py fixture --layers layers.txt`. Result: 12 modules, 3 import edges, 1 breach (proven), 2 dead modules and 4 unused definitions (suspected). The run with `--entry app.routes.web` gave the same result. The suspected list is the script's guess; the tables above are what survived checking.
- I put the layers file and tracer in `../tte-audit-work/`, outside the fixture. The script won't run under `python -I`, because that flag stops it finding its own helper module (`_encoding`), so I ran it normally from that neutral directory.
- **Search (check 1):** I grepped the whole tree for every candidate name, plus `import_module`, `getattr`, `__import__` and `ENABLED_PLUGINS`. The only dynamic lookup is in the registry, and it names `csv_out` only.
- **Tracer (check 3):** I imported `app.routes.web` and `app.registry`, called `handle()` and `load()`, and diffed the loaded modules. Loaded: `app.models.order`, `app.services.orders`, `app.routes.web`, `app.registry`, `app.plugins.csv_out`. Never loaded: `notify` and `legacy_export`.

### Noted, not chased
- Nothing in the repo calls `app/registry.py: load()`. Presumably whatever runs the app calls it from outside. Confirm that before treating the plugin system as live in production.

I didn't change anything in `fixture/`. If you confirm that no outside service or script uses `legacy_export` or `notify`, I can delete each one in its own commit with this proof attached, so either can be undone in one step.