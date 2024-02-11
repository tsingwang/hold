FUTURES = {
    "IH": {
        "unit": 300,
        "ratio": 0.12,
    },
    "IF": {
        "unit": 300,
        "ratio": 0.12,
    },
    "IC": {
        "unit": 200,
        "ratio": 0.12,
    },
    "IM": {
        "unit": 200,
        "ratio": 0.12,
    },
}

def get_future_info(code):
    for k, v in FUTURES.items():
        if code.startswith(k):
            return v
    return None
