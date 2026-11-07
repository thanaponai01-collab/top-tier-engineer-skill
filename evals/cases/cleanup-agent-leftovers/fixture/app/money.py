def parse_amount(text):
    """'12.34' or '-5' -> cents as an int."""
    text = text.strip().replace("$", "").replace(",", "")
    negative = text.startswith("-")
    whole, _, frac = text.lstrip("-").partition(".")
    cents = int(whole or "0") * 100 + int((frac + "00")[:2])
    return -cents if negative else cents


def format_money(cents):
    sign = "-" if cents < 0 else ""
    cents = abs(cents)
    return f"{sign}${cents // 100}.{cents % 100:02d}"
