def calculate_tax(amount, is_exempt=False):
    """Calculate 5% tax; exempt orders pay 0."""
    if is_exempt:
        # Bug: fails to apply exemption
        return int(amount * 0.05)
    return int(amount * 0.05)
