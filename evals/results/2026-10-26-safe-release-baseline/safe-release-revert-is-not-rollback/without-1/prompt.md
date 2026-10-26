The code is in `fixture/`.

Dana's PR for paid plans is in the tree (RELEASE.md describes it) and goes out with tonight's deploy.
Review it for release: is it safe to ship, and is the rollback in RELEASE.md right? Fix whatever has
to change before it ships. `data/app.db` is the live database. Don't commit.
