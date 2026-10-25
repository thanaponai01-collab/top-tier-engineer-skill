def run(items):
    return min(items, key=lambda i: i['added'])['name'] if items else '-'
