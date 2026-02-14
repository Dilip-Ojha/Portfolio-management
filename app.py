import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent))

import streamlit as st
import pandas as pd

from core.database import initialize_database
from core.transactions import add_transaction, get_all_transactions, delete_transaction

st.set_page_config(page_title="NEPSE Portfolio Manager", layout="wide")


def main():
    st.title("📈 NEPSE Portfolio Manager (SEBON Rules Based)")
    st.write("A personal portfolio tracker with tax, fees, and performance analytics.")

    initialize_database()

    st.subheader("➕ Add Transaction")

    with st.form("transaction_form"):
        col1, col2, col3 = st.columns(3)

        with col1:
            trade_date = st.date_input("Trade Date")
            symbol = st.text_input("Stock Symbol (e.g., NABIL)")

        with col2:
            trade_type = st.selectbox("Trade Type", ["BUY", "SELL"])
            quantity = st.number_input("Quantity", min_value=1, step=1)

        with col3:
            price = st.number_input("Price", min_value=1.0, step=0.5)
            remarks = st.text_input("Remarks (optional)")

        submitted = st.form_submit_button("Add Transaction")

        if submitted:
            try:
                add_transaction(
                    trade_date=str(trade_date),
                    symbol=symbol,
                    trade_type=trade_type,
                    quantity=quantity,
                    price=price,
                    remarks=remarks
                )
                st.success("Transaction added successfully!")
            except Exception as e:
                st.error(f"Error: {e}")

    st.divider()

    st.subheader("📜 Transaction History")

    transactions = get_all_transactions()

    if transactions:
        df = pd.DataFrame(transactions)
        st.dataframe(df, use_container_width=True)

        st.subheader("🗑️ Delete Transaction")
        delete_id = st.number_input("Enter Transaction ID to delete", min_value=1, step=1)

        if st.button("Delete"):
            try:
                delete_transaction(delete_id)
                st.success(f"Transaction ID {delete_id} deleted successfully.")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

    else:
        st.info("No transactions found. Add your first transaction above.")


if __name__ == "__main__":
    main()
