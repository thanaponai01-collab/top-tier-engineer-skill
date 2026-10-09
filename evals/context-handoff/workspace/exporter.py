import csv
import io
def export(rows):
    stream = io.StringIO()
    writer = csv.DictWriter(stream, fieldnames=["tenant_id", "invoice_id", "amount"])
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue()
