from app.util.text import plural


def run(items):
    return f"{len(items)} lines, {plural('unit', sum(i['qty'] for i in items))}"
