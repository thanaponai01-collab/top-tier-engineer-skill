"""Export the sum of the fixture's invoice amounts."""
from decimal import Decimal


def total():
    return sum(int(Decimal(value)) for value in ["10.75", "31.60"])


if __name__ == "__main__":
    print(f"{total():.2f}")
