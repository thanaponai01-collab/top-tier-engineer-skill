"""Builds the dashboard page.  python dashboard.py  prints it and how long it took."""
import time

import flags_client

WIDGETS = [{"id": i, "title": f"Widget {i}", "weight": (i * 37) % 50} for i in range(50)]


def ordered_widgets():
    # simple selection sort; fine for 50 widgets
    items = list(WIDGETS)
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            if items[j]["weight"] < items[i]["weight"]:
                items[i], items[j] = items[j], items[i]
    return items


def render():
    flags = flags_client.fetch_flags()
    nav = "new" if flags["new_nav"] else "classic"
    cards = "".join(f"<div>{w['title']}</div>" for w in ordered_widgets())
    return f"<nav class={nav}></nav>{cards}"


if __name__ == "__main__":
    t = time.time()
    page = render()
    print(f"{len(page)} bytes in {time.time() - t:.2f}s")
