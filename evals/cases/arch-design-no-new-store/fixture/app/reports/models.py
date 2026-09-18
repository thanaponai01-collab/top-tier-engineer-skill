from app.db import execute


def list_reports(owner_id):
    return execute(
        "SELECT id, title, created_at FROM reports WHERE owner_id = ?", (owner_id,)
    )


def get_report(report_id):
    rows = execute(
        "SELECT id, title, created_at, body FROM reports WHERE id = ?", (report_id,)
    )
    return rows[0] if rows else None
