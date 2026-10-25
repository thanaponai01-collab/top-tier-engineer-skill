def run(items):
    return f"{sum(i['qty'] for i in items)} units across {len(items)} lines"
