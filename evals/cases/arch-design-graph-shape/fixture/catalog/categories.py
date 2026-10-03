from core.util import clamp, as_cents, slug, first


TREE = {}


def add_category(name, parent=None):
    TREE[slug(name)] = parent
    return slug(name)


def parent_of(cat):
    return TREE.get(cat)


def depth(cat):
    return 0 if TREE.get(cat) is None else 1 + depth(TREE[cat])
