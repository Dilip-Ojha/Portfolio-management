import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def load_rules():
    rules_path = PROJECT_ROOT / "config" / "rules.json"
    if not rules_path.exists():
        raise FileNotFoundError(f"Rules file not found: {rules_path}")

    with open(rules_path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_symbol(symbol: str) -> str:
    if not symbol:
        raise ValueError("Stock symbol cannot be empty.")

    symbol = symbol.strip().upper()

    if not symbol.isalnum():
        raise ValueError("Stock symbol must contain only letters/numbers (no spaces).")

    if len(symbol) < 2 or len(symbol) > 15:
        raise ValueError("Stock symbol length must be between 2 and 15 characters.")

    return symbol


def validate_quantity(qty: int) -> int:
    try:
        qty = int(qty)
    except Exception:
        raise ValueError("Quantity must be an integer.")

    if qty <= 0:
        raise ValueError("Quantity must be greater than 0.")

    return qty


def validate_price(price: float) -> float:
    try:
        price = float(price)
    except Exception:
        raise ValueError("Price must be a number.")

    if price <= 0:
        raise ValueError("Price must be greater than 0.")

    return round(price, 2)


def validate_trade_type(trade_type: str) -> str:
    if not trade_type:
        raise ValueError("Trade type cannot be empty.")

    trade_type = trade_type.strip().upper()

    if trade_type not in ["BUY", "SELL"]:
        raise ValueError("Trade type must be either BUY or SELL.")

    return trade_type
