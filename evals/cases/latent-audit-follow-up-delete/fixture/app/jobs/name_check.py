def run(items):
    bad = [i['name'] for i in items if i['name'] != i['name'].strip()]
    return f"{len(bad)} names with stray spaces"
