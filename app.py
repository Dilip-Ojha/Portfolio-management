import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent))

import streamlit as st
import pandas as pd

from core.database import initialize_database
from core.transactions import add_transaction, get_all_transactions, delete_transaction
from core.pricing import fetch_live_prices
from core.portfolio_live import calculate_portfolio_with_live_prices


st.set_page_config(page_title="NEPSE Portfolio Manager", layout="wide")


@st.cache_data(ttl=60)
def cached_prices():
    """
    Cache NEPSE prices for 60 seconds.
    Prevents too many requests.
    """
    return fetch_live_prices()


def main():
    st.title("📈 NEPSE Portfolio Manager (SEBON Rules Based)")
    st.caption("Track holdings, profit/loss, commissions, taxes, and live portfolio performance.")

    initialize_database()

    st.sidebar.header("⚙️ Settings")
    investor_type = st.sidebar.selectbox("Investor Type", ["individual", "institution"])

    st.sidebar.divider()
    if st.sidebar.button("🔄 Refresh Live Prices"):
        cached_prices.clear()
        st.rerun()

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
                st.success("✅ Transaction added successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error: {e}")

    st.divider()

    st.subheader("📜 Transaction History")
    transactions = get_all_transactions()

    if transactions:
        df_tx = pd.DataFrame(transactions)
        st.dataframe(df_tx, width="stretch")


        with st.expander("🗑️ Delete Transaction"):
            delete_id = st.number_input("Enter Transaction ID to delete", min_value=1, step=1)

            if st.button("Delete Transaction"):
                try:
                    delete_transaction(delete_id)
                    st.success(f"Transaction ID {delete_id} deleted successfully.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
    else:
        st.info("No transactions found. Add your first transaction above.")

    st.divider()

    st.subheader("📌 Live Portfolio Summary")

    try:
        prices = cached_prices()
        portfolio_data = calculate_portfolio_with_live_prices(prices, investor_type=investor_type)

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("📊 Market Value", portfolio_data["total_market_value"])
        col2.metric("💼 Remaining Cost", portfolio_data["total_cost_remaining"])
        col3.metric("📈 Unrealized Profit", portfolio_data["total_unrealized_profit"])
        col4.metric("💰 Realized Profit", portfolio_data["total_realized_profit"])

        st.divider()

        st.subheader("🏦 Total Portfolio Performance")
        st.metric("🔥 Total Profit (Realized + Unrealized)", portfolio_data["total_profit"])

        st.divider()

        st.subheader("📦 Holdings with Live LTP")

        df_holdings = pd.DataFrame(portfolio_data["enhanced_holdings"])
        if not df_holdings.empty:
            st.dataframe(df_holdings, use_container_width=True)

            st.subheader("📌 Portfolio Allocation (Market Value)")
            alloc_df = df_holdings[["symbol", "market_value"]].copy()
            alloc_df = alloc_df[alloc_df["market_value"] > 0]

            if not alloc_df.empty:
                st.bar_chart(alloc_df.set_index("symbol"))
            else:
                st.info("No market value to plot yet.")

        else:
            st.info("No holdings found yet.")

        st.divider()

        st.subheader("💰 Realized Profit Report (Sell Transactions)")
        if portfolio_data["realized_summary"]:
            df_realized = pd.DataFrame(portfolio_data["realized_summary"])
            st.dataframe(df_realized, use_container_width=True)
        else:
            st.info("No SELL transactions yet. Realized profit will appear after selling shares.")

    except Exception as e:
        st.error(f"Live Portfolio Error: {e}")
        st.info("NEPSE site may be down or its structure changed. We can update scraper if needed.")


if __name__ == "__main__":
    main()
