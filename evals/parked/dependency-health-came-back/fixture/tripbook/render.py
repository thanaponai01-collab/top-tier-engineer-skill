import os

from jinja2 import Environment, FileSystemLoader, contextfilter

from tripbook import times

TEMPLATES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templates")


@contextfilter
def local_time(ctx, moment):
    return times.to_local(moment, ctx["home_tz"]).strftime("%a %d %b %H:%M")


def itinerary_html(name, legs, home_tz):
    env = Environment(loader=FileSystemLoader(TEMPLATES), autoescape=True)
    env.filters["local_time"] = local_time
    return env.get_template("itinerary.html").render(name=name, legs=legs, home_tz=home_tz)
