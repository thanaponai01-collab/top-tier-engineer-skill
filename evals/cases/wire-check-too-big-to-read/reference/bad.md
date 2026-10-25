Nothing imports the command modules directly, but the registry loads them. Unreached: bins_rebalance
(not registered), crossdock (flag off), purge_audit (not scheduled). Both bin alert handlers are dead:
on_bin_low is never called, and neither handler's event is published anywhere.
