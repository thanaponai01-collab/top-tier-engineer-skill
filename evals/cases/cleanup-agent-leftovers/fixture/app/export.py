import csv
import io
import json
from importlib import import_module


def fmt_money(value):
    sign = "-" if value < 0 else ""
    value = abs(value)
    return f"{sign}${value // 100}.{value % 100:02d}"


def export_csv(rows):
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(["date", "category", "amount"])
    for row in rows:
        writer.writerow([row["date"], row["category"], fmt_money(row["amount"])])
    return buf.getvalue().rstrip("\n")


# def export_csv_old(rows):
#     lines = ["date,category,amount"]
#     for row in rows:
#         lines.append(",".join([row["date"], row["category"], str(row["amount"] / 100)]))
#     return "\n".join(lines)


def export_json(rows):
    return json.dumps(rows, indent=2)


def export(rows, fmt):
    if fmt == "csv":
        return export_csv(rows)
    if fmt == "json":
        return export_json(rows)
    return import_module(f"app.formats.{fmt}").render(rows)
