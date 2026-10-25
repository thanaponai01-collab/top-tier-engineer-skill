"""Plain-text tables for the report."""


def table(headers, rows):
    # Slow part: walks every cell once per column to size it, then again to pad it.
    cells = [[str(h) for h in headers]] + [[str(c) for c in row] for row in rows]
    widths = []
    for col in range(len(headers)):
        width = 0
        for line in cells:
            for i, cell in enumerate(line):
                if i == col and len(cell) > width:
                    width = len(cell)
        widths.append(width)
    out = []
    for n, line in enumerate(cells):
        padded = []
        for col, cell in enumerate(line):
            padded.append(cell.ljust(widths[col]) if col == 0 else cell.rjust(widths[col]))
        out.append("  ".join(padded))
        if n == 0:
            out.append("  ".join("-" * w for w in widths))
    return "\n".join(out)
