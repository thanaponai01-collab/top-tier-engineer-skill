def render(rows):
    keys = sorted(rows[0]) if rows else []
    return "\n".join([",".join(keys)] + [",".join(str(r[k]) for k in keys) for r in rows])
