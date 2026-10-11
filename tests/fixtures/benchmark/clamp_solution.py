def clamp(value, lower, upper):
    if lower > upper:
        raise ValueError("invalid bounds")
    return min(upper, max(lower, value))
