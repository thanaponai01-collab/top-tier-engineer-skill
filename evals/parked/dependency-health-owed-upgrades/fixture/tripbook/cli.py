import click

from tripbook import itinerary, loader, rates, render


@click.group()
def main():
    """Trip file in, itinerary out."""


@main.command("render")
@click.argument("trip_file")
def render_cmd(trip_file):
    trip = loader.load(trip_file)
    legs = itinerary.ordered_legs(trip["legs"])
    click.echo(render.itinerary_html(trip["name"], legs, trip.get("home_tz", "UTC")))


@main.command("rates")
@click.argument("currency")
def rates_cmd(currency):
    for code, value in sorted(rates.fetch(currency).items()):
        click.echo(f"{code} {value:.4f}")
