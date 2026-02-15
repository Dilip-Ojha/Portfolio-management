from datetime import datetime
from core.transactions import get_all_transactions
from core.charges import (
    calculate_total_buy_cost,
    calculate_total_sell_deductions,
    calculate_capital_gain_tax
)


def calculate_portfolio(investor_type: str = "individual") -> dict:
    """
    Returns:
    - holdings summary
    - realized profit
    - unrealized profit (needs current price)
    - transaction level charges summary
    """

    transactions = get_all_transactions()

    # Grouped FIFO lots per symbol
    fifo_lots = {}  # {symbol: [ {qty, price, date} ]}

    holdings = {}  # {symbol: {...}}
    realized_summary = []
    total_realized_profit = 0.0
    total_tax_paid = 0.0

    for tx in transactions:
        symbol = tx["symbol"]
        trade_type = tx["trade_type"]
        qty = int(tx["quantity"])
        price = float(tx["price"])
        trade_date = tx["trade_date"]

        amount = qty * price

        if symbol not in fifo_lots:
            fifo_lots[symbol] = []

        if symbol not in holdings:
            holdings[symbol] = {
                "symbol": symbol,
                "total_bought_qty": 0,
                "total_sold_qty": 0,
                "remaining_qty": 0,
                "total_buy_amount": 0.0,
                "total_sell_amount": 0.0,
                "avg_buy_price": 0.0
            }

        # BUY transaction
        if trade_type == "BUY":
            buy_costs = calculate_total_buy_cost(amount)

            # effective cost includes commission/fees
            effective_cost = amount + buy_costs["total_extra_cost"]

            fifo_lots[symbol].append({
                "qty": qty,
                "price": price,
                "date": trade_date,
                "effective_cost": effective_cost
            })

            holdings[symbol]["total_bought_qty"] += qty
            holdings[symbol]["total_buy_amount"] += effective_cost
            holdings[symbol]["remaining_qty"] += qty

        # SELL transaction
        elif trade_type == "SELL":
            if holdings[symbol]["remaining_qty"] < qty:
                raise ValueError(
                    f"Invalid SELL: Not enough holdings for {symbol}. "
                    f"Trying to sell {qty} but only {holdings[symbol]['remaining_qty']} available."
                )

            sell_deductions = calculate_total_sell_deductions(amount)
            net_sell_amount = amount - sell_deductions["total_deductions"]

            holdings[symbol]["total_sold_qty"] += qty
            holdings[symbol]["total_sell_amount"] += net_sell_amount
            holdings[symbol]["remaining_qty"] -= qty

            # FIFO matching
            remaining_to_sell = qty
            sell_profit = 0.0
            sell_tax = 0.0

            while remaining_to_sell > 0:
                lot = fifo_lots[symbol][0]

                lot_qty = lot["qty"]
                lot_price = lot["price"]
                lot_date = lot["date"]

                used_qty = min(lot_qty, remaining_to_sell)

                # Cost basis for this portion (proportional effective cost)
                lot_effective_cost = lot["effective_cost"]
                cost_per_share = lot_effective_cost / lot_qty
                cost_basis = used_qty * cost_per_share

                # Sell proceeds for this portion (proportional)
                proceeds_per_share = net_sell_amount / qty
                proceeds = used_qty * proceeds_per_share

                profit_piece = proceeds - cost_basis

                # Holding days for tax
                buy_dt = datetime.strptime(lot_date, "%Y-%m-%d")
                sell_dt = datetime.strptime(trade_date, "%Y-%m-%d")
                holding_days = (sell_dt - buy_dt).days

                tax_piece = calculate_capital_gain_tax(
                    profit=profit_piece,
                    holding_days=holding_days,
                    investor_type=investor_type
                )

                sell_profit += profit_piece
                sell_tax += tax_piece

                # Reduce lot qty
                lot["qty"] -= used_qty
                lot["effective_cost"] -= cost_basis

                remaining_to_sell -= used_qty

                # Remove lot if empty
                if lot["qty"] == 0:
                    fifo_lots[symbol].pop(0)

            # Apply tax on realized profit
            net_profit_after_tax = sell_profit - sell_tax

            total_realized_profit += net_profit_after_tax
            total_tax_paid += sell_tax

            realized_summary.append({
                "symbol": symbol,
                "sell_date": trade_date,
                "quantity_sold": qty,
                "gross_sell_amount": round(amount, 2),
                "net_sell_amount": round(net_sell_amount, 2),
                "broker_commission": sell_deductions["broker_commission"],
                "sebon_fee": sell_deductions["sebon_fee"],
                "dp_charge": sell_deductions["dp_charge"],
                "capital_gain_tax": round(sell_tax, 2),
                "profit_before_tax": round(sell_profit, 2),
                "profit_after_tax": round(net_profit_after_tax, 2)
            })

        else:
            raise ValueError(f"Unknown trade_type: {trade_type}")

    # Compute average buy price
    for sym, h in holdings.items():
        if h["total_bought_qty"] > 0:
            h["avg_buy_price"] = round(h["total_buy_amount"] / h["total_bought_qty"], 2)
        else:
            h["avg_buy_price"] = 0.0

    return {
        "holdings": holdings,
        "realized_summary": realized_summary,
        "total_realized_profit": round(total_realized_profit, 2),
        "total_tax_paid": round(total_tax_paid, 2)
    }
