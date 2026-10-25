def run(items):
    return max(items, key=lambda i: i['added'])['name'] if items else '-'
