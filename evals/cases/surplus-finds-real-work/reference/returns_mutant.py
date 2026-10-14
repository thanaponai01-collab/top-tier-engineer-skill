RETURN_WINDOW_DAYS = 30


def can_return(days_since_delivery, opened):
    return days_since_delivery < RETURN_WINDOW_DAYS and not opened
