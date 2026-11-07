"""Web preview, served by gunicorn (see Dockerfile). A plain WSGI app."""


def app(environ, start_response):
    start_response("200 OK", [("Content-Type", "text/plain; charset=utf-8")])
    return [b"tripbook preview: POST a trip file to /render\n"]
