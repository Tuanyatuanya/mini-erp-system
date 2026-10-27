from datetime import date


def make_plan_no() -> str:
    today = date.today()
    import random, string
    suffix = "".join(random.choices(string.digits, k=5))
    return f"PP-{today.strftime('%Y%m')}-{suffix}"


def make_output_no() -> str:
    today = date.today()
    import random, string
    suffix = "".join(random.choices(string.digits, k=5))
    return f"OUT-{today.strftime('%Y%m%d')}-{suffix}"


def make_movement_no(mtype: str) -> str:
    today = date.today()
    import random, string
    suffix = "".join(random.choices(string.digits, k=5))
    prefix_map = {
        "RECEIPT": "REC", "ISSUE": "ISS", "RETURN": "RTN",
        "ADJUSTMENT": "ADJ", "TRANSFER": "TRF",
        "PRODUCTION_IN": "PIN", "PRODUCTION_OUT": "POUT",
    }
    prefix = prefix_map.get(mtype, "MOV")
    return f"{prefix}-{today.strftime('%Y%m%d')}-{suffix}"
