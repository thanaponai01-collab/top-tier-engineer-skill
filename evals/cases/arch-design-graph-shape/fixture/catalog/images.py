from core.util import clamp, as_cents, slug, first


def thumb_name(sku, size):
    return f'{sku}_{clamp(size, 16, 512)}.png'


def alt_text(title):
    return title.strip().capitalize()
