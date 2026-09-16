"""The route table. Every request reaches a handler through this dict."""
from handlers import health

ROUTES = {
    "/health": health.check,
}
