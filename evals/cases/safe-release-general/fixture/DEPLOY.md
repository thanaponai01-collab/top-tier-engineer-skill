# Deploying the shop

Production runs on this box: the web app (`shop-web`) and the invoice worker (`shop-worker`), both
reading `data/shop.db`.

`./deploy.sh` does, in order:

1. `git pull`
2. `python migrate.py up`
3. restart `shop-web` (a few seconds)
4. restart `shop-worker`. The worker finishes the batch it is on before it restarts, which takes up
   to 40 minutes on a busy evening, so for that long the old worker code runs against the new schema.

Rollback: `git checkout <previous tag> && ./deploy.sh`.

The nightly invoice run starts at 23:00. Deploys go out at 21:00.
