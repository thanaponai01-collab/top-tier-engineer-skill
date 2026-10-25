def run(items):
    return str(sum(i['qty'] for i in items))
