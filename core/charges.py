from utils.helpers import load_rules


def calculate_broker_commission(amount: float) -> float:
    """
    Calculates broker commission based on slab rules.
    """
    rules = load_rules()
    broker_rules = rules["broker_commission"]

    slabs = broker_rules["slabs"]
    minimum_commission = broker_rules.get("minimum_commission", 0)

    if amount <= 0:
        return 0.0

    commission_rate = None

    for slab in slabs:
        slab_min = slab["min"]
        slab_max = slab["max"]
        rate = slab["rate"]

        if slab_max is None:
            if amount >= slab_min:
                commission_rate = rate
                break
        else:
            if slab_min <= amount < slab_max:
                commission_rate = rate
                break

    if commission_rate is None:
        raise ValueError("No broker commission slab matched. Check rules.json.")

    commission = amount * commission_rate

    if commission < minimum_commission:
        commission = minimum_commission

    return round(commission, 2)


def calculate_sebon_fee(amount: float) -> float:
    """
    SEBON regulatory fee based on trade amount.
    """
    rules = load_rules()
    rate = rules.get("sebon_fee_rate", 0)

    if amount <= 0:
        return 0.0

    return round(amount * rate, 2)


def get_dp_charge() -> float:
    """
    DP charge is usually fixed per transaction.
    """
    rules = load_rules()
    return float(rules.get("dp_charge", 0))


def calculate_capital_gain_tax(profit: float, holding_days: int,
                               investor_type: str = "individual") -> float:
    """
    Calculates capital gain tax based on holding period and investor type.
    profit: positive realized profit only (loss = 0 tax)
    holding_days: number of days between buy and sell
    investor_type: individual/institution
    """
    rules = load_rules()
    tax_rules = rules["capital_gain_tax"].get(investor_type.lower())

    if tax_rules is None:
        raise ValueError(f"Invalid investor_type '{investor_type}'. Use individual/institution.")

    if profit <= 0:
        return 0.0

    long_term_days = tax_rules["long_term_days"]

    if holding_days >= long_term_days:
        rate = tax_rules["long_term_rate"]
    else:
        rate = tax_rules["short_term_rate"]

    return round(profit * rate, 2)


def calculate_total_sell_deductions(amount: float) -> dict:
    """
    Returns broker commission + SEBON fee + DP charge for a SELL trade.
    """
    broker = calculate_broker_commission(amount)
    sebon = calculate_sebon_fee(amount)
    dp = get_dp_charge()

    total = broker + sebon + dp

    return {
        "broker_commission": broker,
        "sebon_fee": sebon,
        "dp_charge": dp,
        "total_deductions": round(total, 2)
    }


def calculate_total_buy_cost(amount: float) -> dict:
    """
    Returns extra costs for BUY trade.
    """
    broker = calculate_broker_commission(amount)
    sebon = calculate_sebon_fee(amount)
    dp = get_dp_charge()

    total = broker + sebon + dp

    return {
        "broker_commission": broker,
        "sebon_fee": sebon,
        "dp_charge": dp,
        "total_extra_cost": round(total, 2)
    }
