"""Prints the daily total. This is where the wrong number is noticed."""
from parse import load
from totals import total


def render(path="data.csv"):
    return f"Total: {total(load(path))}"


if __name__ == "__main__":
    print(render())
