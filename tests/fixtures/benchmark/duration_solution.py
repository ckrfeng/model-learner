def duration_seconds(text):
    text = text.strip()
    if not text or text[-1] not in "smh" or not text[:-1].isdigit():
        raise ValueError("invalid duration")
    return int(text[:-1]) * {"s": 1, "m": 60, "h": 3600}[text[-1]]
