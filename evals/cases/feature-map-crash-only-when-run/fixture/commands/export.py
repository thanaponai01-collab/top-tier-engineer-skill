import csv

COLUMNS = ["id", "title", "body"]


def run(store, args):
    with open(args.path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=COLUMNS)
        writer.writeheader()
        for note in store.all():
            writer.writerow(note)
    print(f"exported to {args.path}")
    return 0
