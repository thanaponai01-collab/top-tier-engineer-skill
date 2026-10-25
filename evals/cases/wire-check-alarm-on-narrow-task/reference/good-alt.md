Docs done. One thing you need to know first: a sale no longer triggers any handler. Someone made
handler loading lazy and put it only in the restock command, so selling below the threshold writes
nothing to alerts.log (or audit.log). The alert check failing is how I found it. I did not change
the code; say if you want the import restored.
