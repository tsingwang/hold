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

def is_future(code):
    for k in FUTURES.keys():
        if code.startswith(k):
            return True
    return False

def is_option(code):
    return True if len(code) > 9 else False

def is_contract(code):
    return is_future(code) or is_option(code)

def contract_unit(code):
    for k, v in FUTURES.items():
        if code.startswith(k):
            return v['unit']
    if is_option(code):
        return 10000
    return 1

def contract_fee(code):
    if is_option(code):
        return 1.7
    return 0
