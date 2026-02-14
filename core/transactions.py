from datetime import datetime
from core.database import get_connection
from utils.helpers import (
    validate_symbol,
    validate_quantity,
    validate_price,
    validate_trade_type
)


def add_transaction(trade_date: str, symbol: str, trade_type: str,
                    quantity: int, price: float, remarks: str = None):
    """
    Adds a new transaction (BUY or SELL).
    """

    # Validate date
    try:
        datetime.strptime(trade_date, "%Y-%m-%d")
    except Exception:
        raise ValueError("trade_date must be in YYYY-MM-DD format.")

    symbol = validate_symbol(symbol)
    trade_type = validate_trade_type(trade_type)
    quantity = validate_quantity(quantity)
    price = validate_price(price)

    if remarks:
        remarks = remarks.strip()
        if len(remarks) > 200:
            raise ValueError("Remarks too long (max 200 characters).")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO transactions (trade_date, symbol, trade_type, quantity, price, remarks)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (trade_date, symbol, trade_type, quantity, price, remarks))

    conn.commit()
    conn.close()


def get_all_transactions():
    """
    Returns all transactions ordered by date.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM transactions
        ORDER BY trade_date ASC, id ASC
    """)

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def delete_transaction(transaction_id: int):
    """
    Deletes a transaction by ID.
    """
    try:
        transaction_id = int(transaction_id)
    except Exception:
        raise ValueError("transaction_id must be an integer.")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
    conn.commit()
    conn.close()
