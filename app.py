import streamlit as st

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="SplitWise Clone",
    page_icon="💸",
    layout="wide"
)

# --- HOME PAGE ---
st.title("💸 Splitwise Clone")
st.write("A full featured expense splitting app built with Python & Streamlit.")

st.divider()

# --- FEATURE CARDS ---
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.info("👥 **Groups**\n\nCreate groups and manage members")

with col2:
    st.info("🧾 **Expenses**\n\nAdd and split expenses")

with col3:
    st.info("⚖️ **Balances**\n\nSee who owes who")

with col4:
    st.info("✅ **Settle Up**\n\nMark debts as paid")

with col5:
    st.info("📊 **Dashboard**\n\nSpending analytics")

st.divider()

# --- QUICK STATS ---
st.subheader("📊 Quick Stats")

import os
import pandas as pd

col1, col2, col3 = st.columns(3)

with col1:
    if os.path.exists("data/groups.csv"):
        groups_df = pd.read_csv("data/groups.csv")
        num_groups = groups_df["Group"].nunique()
    else:
        num_groups = 0
    st.metric("👥 Total Groups", num_groups)

with col2:
    if os.path.exists("data/expenses.csv"):
        expenses_df = pd.read_csv("data/expenses.csv")
        num_expenses = expenses_df["Expense"].nunique() if "Expense" in expenses_df.columns else 0
    else:
        num_expenses = 0
    st.metric("🧾 Total Expenses", num_expenses)

with col3:
    if os.path.exists("data/settlements.csv"):
        settlements_df = pd.read_csv("data/settlements.csv")
        num_settlements = len(settlements_df)
    else:
        num_settlements = 0
    st.metric("✅ Total Settlements", num_settlements)

st.divider()

st.caption("Built with Python & Streamlit 🐍 by SharathReddy — github.com/SharathReddyKottam/split-it")