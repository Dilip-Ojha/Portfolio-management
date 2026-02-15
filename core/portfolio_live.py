from core.portfolio import calculate_portfolio


def calculate_portfolio_with_live_prices(prices: dict, investor_type="individual") -> dict:
    """
    Adds live price-based calculations to holdings.
    """

    portfolio_data = calculate_portfolio(investor_type=investor_type)
    holdings = portfolio_data["holdings"]

    total_market_value = 0.0
    total_cost_remaining = 0.0
    total_unrealized_profit = 0.0

    enhanced_holdings = []

    for symbol, h in holdings.items():
        remaining_qty = h["remaining_qty"]

        ltp = prices.get(symbol)
        if ltp is None:
            ltp = 0.0  # if price not found

        current_value = remaining_qty * ltp

        # remaining cost = avg_buy_price * remaining_qty
        remaining_cost = remaining_qty * h["avg_buy_price"]

        unrealized_profit = current_value - remaining_cost

        total_market_value += current_value
        total_cost_remaining += remaining_cost
        total_unrealized_profit += unrealized_profit

        enhanced_holdings.append({
            "symbol": symbol,
            "remaining_qty": remaining_qty,
            "avg_buy_price": h["avg_buy_price"],
            "ltp": round(ltp, 2),
            "cost_value": round(remaining_cost, 2),
            "market_value": round(current_value, 2),
            "unrealized_profit": round(unrealized_profit, 2),
            "unrealized_profit_percent": round((unrealized_profit / remaining_cost) * 100, 2)
            if remaining_cost > 0 else 0.0
        })

    portfolio_data["enhanced_holdings"] = enhanced_holdings
    portfolio_data["total_market_value"] = round(total_market_value, 2)
    portfolio_data["total_cost_remaining"] = round(total_cost_remaining, 2)
    portfolio_data["total_unrealized_profit"] = round(total_unrealized_profit, 2)

    total_profit = portfolio_data["total_realized_profit"] + total_unrealized_profit
    portfolio_data["total_profit"] = round(total_profit, 2)

    return portfolio_data
