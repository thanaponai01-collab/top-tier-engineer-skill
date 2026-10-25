def run(items):
    return ', '.join(i['name'] for i in items if i['qty'] == 0) or '-'
