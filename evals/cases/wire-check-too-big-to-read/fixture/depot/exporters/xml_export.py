def render(rows):
    items = "".join("<row " + " ".join(f'{k}="{v}"' for k, v in sorted(r.items())) + "/>" for r in rows)
    return f"<rows>{items}</rows>"
