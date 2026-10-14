GOLD_FROM = 1000
SILVER_FROM = 250


def tier(points):
    if points >= GOLD_FROM:
        return "gold"
    if points > SILVER_FROM:
        return "silver"
    return "member"


def points_for(total):
    return int(total)
