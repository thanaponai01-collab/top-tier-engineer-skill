from payments.live import LiveGateway
from services.order_service import place
from api.auth import current_account
from api.schemas import order_in, order_out


def post_order(token, body):
    acct = current_account(token)
    data = order_in(body)
    return order_out(place(acct['id'], data['items'], LiveGateway(), data['code']))
