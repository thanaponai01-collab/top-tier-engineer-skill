from app import export_allowed


def batch_allowed(rows):
    """Billing jobs share the export boundary, though the area map omits this caller."""
    return export_allowed(rows)
