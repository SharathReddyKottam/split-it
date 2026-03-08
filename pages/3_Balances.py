import streamlit as st
import pandas as pd
import plotly.express as px
from utils.file_helpers import load_groups, load_expenses, load_settlements
from utils.calculations import calculate_balances

# --- PAGE CONFIG ---
st.set_page_config(page_title="Balances", page_icon="⚖️", layout="centered")

st.title("⚖️ Balances")
st.write("See exactly who owes who across all expenses.")

st.divider()

# --- LOAD DATA ---
groups_df = load_groups()

if groups_df.empty:
    st.warning("⚠️ No groups found. Please create a group first!")
    st.stop()

# --- SELECT GROUP ---
group_names = groups_df["Group"].unique().tolist()
selected_group = st.selectbox("Select a group", group_names)

st.divider()

# --- LOAD EXPENSES & SETTLEMENTS ---
expenses_df = load_expenses()
settlements_df = load_settlements()

group_expenses = expenses_df[expenses_df["Group"] == selected_group]

if group_expenses.empty:
    st.info("No expenses found for this group. Add some expenses first!")
    st.stop()

# --- CALCULATE BALANCES ---
balances_df = calculate_balances(expenses_df, settlements_df, selected_group)

st.subheader(f"💰 Net Balances — '{selected_group}'")

# --- COLOR CODE BALANCES ---
def color_balance(val):
    if val > 0:
        return "color: green"
    elif val < 0:
        return "color: red"
    else:
        return "color: gray"

styled_df = balances_df.style.applymap(color_balance, subset=["Balance ($)"])
st.dataframe(styled_df, use_container_width=True)

st.divider()

# --- WHO OWES WHO ---
st.subheader("🔄 Detailed Breakdown")

members = groups_df[groups_df["Group"] == selected_group]["Member"].tolist()

# calculate what each person owes each other person
owes_data = []

for _, expense_row in group_expenses.iterrows():
    paid_by = expense_row["Paid By"]
    member = expense_row["Member"]
    share = expense_row["Share ($)"]

    if member != paid_by:
        owes_data.append({
            "Who": member,
            "Owes": paid_by,
            "Amount ($)": share,
            "For": expense_row["Expense"]
        })

if owes_data:
    owes_df = pd.DataFrame(owes_data)

    # group by who owes who and sum amounts
    summary = owes_df.groupby(["Who", "Owes"])["Amount ($)"].sum().reset_index()
    summary["Amount ($)"] = summary["Amount ($)"].round(2)

    # subtract settlements
    settlements_group = settlements_df[settlements_df["Group"] == selected_group]
    for _, s in settlements_group.iterrows():
        mask = (summary["Who"] == s["From"]) & (summary["Owes"] == s["To"])
        if mask.any():
            summary.loc[mask, "Amount ($)"] -= s["Amount ($)"]

    # remove settled debts
    summary = summary[summary["Amount ($)"] > 0.01]

    if summary.empty:
        st.success("🎉 All debts are settled!")
    else:
        for _, row in summary.iterrows():
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                st.error(f"👤 **{row['Who']}**")
            with col2:
                st.success(f"💸 owes **{row['Owes']}**")
            with col3:
                st.metric("", f"${row['Amount ($)']:.2f}")

else:
    st.info("No debts found — everyone paid for themselves!")

st.divider()

# --- BALANCE CHART ---
st.subheader("📊 Balance Chart")

fig = px.bar(
    balances_df,
    x="Member",
    y="Balance ($)",
    color="Balance ($)",
    color_continuous_scale=["red", "lightgray", "green"],
    title="Net balance per person (green = owed money, red = owes money)",
    text="Balance ($)"
)

fig.update_traces(texttemplate="$%{text:.2f}", textposition="outside")
fig.update_layout(
    showlegend=False,
    yaxis_range=[
        balances_df["Balance ($)"].min() * 1.4,
        balances_df["Balance ($)"].max() * 1.4
    ]
)

st.plotly_chart(fig, use_container_width=True)

st.divider()

# --- EXPENSE BREAKDOWN ---
st.subheader("📋 All Expenses Breakdown")

display_cols = ["Date", "Expense", "Category", "Paid By", "Member", "Share ($)"]
st.dataframe(group_expenses[display_cols], use_container_width=True)