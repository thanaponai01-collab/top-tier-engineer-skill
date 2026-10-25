def run(items):
    return ', '.join(i['name'] for i in sorted(items, key=lambda i: -i['qty'])[:3])
