"""CSV export for the support lead's spreadsheet."""
import csv
import io

COLUMNS = ["id", "subject", "requester", "channel", "state", "priority", "assignee", "created_at", "solved_at"]


def to_csv(tickets):
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(COLUMNS)
    for t in sorted(tickets, key=lambda t: t.id):
        w.writerow([getattr(t, c) if getattr(t, c) is not None else "" for c in COLUMNS])
    return buf.getvalue()
