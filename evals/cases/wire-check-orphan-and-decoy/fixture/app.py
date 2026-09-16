"""Web entry point. The process starts here and nowhere else in this file tree."""
from routes import ROUTES


def dispatch(path):
    handler = ROUTES.get(path)
    if handler is None:
        return 404, "not found"
    return handler()


if __name__ == "__main__":
    print(dispatch("/health"))
