import yaml


def load(path):
    with open(path, encoding="utf-8") as f:
        trip = yaml.safe_load(f)
    if "legs" not in trip:
        raise ValueError(f"{path}: a trip needs at least one leg")
    return trip
