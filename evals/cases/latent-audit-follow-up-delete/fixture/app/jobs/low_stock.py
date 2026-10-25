def run(items):
    return ', '.join(i['name'] for i in items if 0 < i['qty'] < 50) or '-'
