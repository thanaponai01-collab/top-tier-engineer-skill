from core.util import as_cents


def order_in(body):
    return {'items': body['items'], 'code': body.get('code')}


def order_out(order):
    return {'id': order['id'], 'total': order['total'], 'status': order['status']}
