"""Write the fixture's export: `python make_data.py <out dir> [scale]`.

Deterministic, so the grader can build a bigger export the same way. About one order in twenty
is sent twice by the export's retry, and a third of those retries carry a different amount: the
first row is the real one.
"""
import csv
import os
import random
import sys

REGIONS = [
    ("AK", "Akita", "0.08"), ("AO", "Aomori", "0.10"), ("CH", "Chiba", "0.10"),
    ("EH", "Ehime", "0.08"), ("FK", "Fukuoka", "0.10"), ("FS", "Fukushima", "0.08"),
    ("GF", "Gifu", "0.10"), ("GU", "Gunma", "0.08"), ("HI", "Hiroshima", "0.10"),
    ("HK", "Hokkaido", "0.08"), ("HY", "Hyogo", "0.10"), ("IB", "Ibaraki", "0.08"),
    ("IS", "Ishikawa", "0.10"), ("IW", "Iwate", "0.08"), ("KA", "Kagawa", "0.10"),
    ("KG", "Kagoshima", "0.08"), ("KN", "Kanagawa", "0.10"), ("KC", "Kochi", "0.08"),
    ("KM", "Kumamoto", "0.10"), ("KY", "Kyoto", "0.10"), ("MI", "Mie", "0.08"),
    ("MY", "Miyagi", "0.10"), ("MZ", "Miyazaki", "0.08"), ("NA", "Nagano", "0.10"),
    ("NS", "Nagasaki", "0.08"), ("NR", "Nara", "0.10"), ("NI", "Niigata", "0.08"),
    ("OI", "Oita", "0.10"), ("OK", "Okayama", "0.08"), ("ON", "Okinawa", "0.05"),
    ("OS", "Osaka", "0.10"), ("SG", "Saga", "0.08"), ("SA", "Saitama", "0.10"),
    ("SH", "Shiga", "0.08"), ("SM", "Shimane", "0.10"), ("SZ", "Shizuoka", "0.08"),
    ("TC", "Tochigi", "0.10"), ("TK", "Tokushima", "0.08"), ("TY", "Tokyo", "0.10"),
    ("TT", "Tottori", "0.08"),
]


def write(out, scale=1):
    rng = random.Random(20261026 + scale)
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "regions.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["code", "name", "tax"])
        w.writerows(REGIONS)
    customers = [f"user{i:04d}@example.com" for i in range(900 * scale)]
    rows = []
    for i in range(12000 * scale):
        row = [f"A{i:06d}", rng.choice(customers), rng.choice(REGIONS)[0],
               f"{rng.randint(300, 25000) / 100:.2f}", f"2026-10-{1 + i * 25 // (12000 * scale):02d}"]
        rows.append(row)
        if rng.random() < 0.05:
            retry = list(row)
            if rng.random() < 0.33:
                retry[3] = f"{rng.randint(300, 25000) / 100:.2f}"
            rows.append(retry)
    with open(os.path.join(out, "orders.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["order_id", "email", "region", "amount", "date"])
        w.writerows(rows)


if __name__ == "__main__":
    write(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 1)
