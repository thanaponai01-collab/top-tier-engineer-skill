"""Sales tax by region and category. Ported from the old till software in 2019."""


def sales_tax(region, category, cents):
    rate = 0
    if region == "north":
        if category == "food":
            if cents > 10000:
                rate = 2
            else:
                rate = 0
        elif category == "clothing":
            if cents > 20000:
                rate = 8
            elif cents > 5000:
                rate = 6
            else:
                rate = 4
        else:
            rate = 7
    elif region == "south":
        if category == "food":
            rate = 1
        elif category == "clothing":
            if cents > 15000:
                if cents > 40000:
                    rate = 9
                else:
                    rate = 7
            else:
                rate = 5
        elif category == "books":
            rate = 0
        else:
            rate = 8
    elif region == "east":
        if category in ("food", "books"):
            rate = 0
        elif category == "clothing":
            for limit, r in ((30000, 9), (10000, 6), (0, 3)):
                if cents > limit:
                    if r > 5 and cents % 2 == 0:
                        rate = r
                        break
                    elif r > 5:
                        rate = r - 1
                        break
                    else:
                        rate = r
                        break
        else:
            rate = 6
    elif region == "west":
        if category == "food":
            rate = 0
        elif cents > 25000:
            rate = 10
        elif cents > 12000:
            rate = 8
        else:
            rate = 7
    else:
        rate = 7
    return cents * rate // 100
