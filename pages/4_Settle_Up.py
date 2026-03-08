import streamlit as st
import pandas as pd
import plotly.express as px
from utils.file_helpers import load_groups, load_expenses, load_settlements, save_settlement
from utils.calculations import calculate_balances

# --- PAGE CONFIG ---
st.set_page_config(page_title="Settle Up", page_icon="✅", layout="centered")

st.title("✅ Settle Up")
st.write("Mark debts as paid and track all settlements.")

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

# --- CURRENT DEBTS ---
st.subheader("💳 Outstanding Debts")

# calculate who owes who
owes_data = []

for _, expense_row in group_expenses.iterrows():
    paid_by = expense_row["Paid By"]
    member = expense_row["Member"]
    share = expense_row["Share ($)"]

    if member != paid_by:
        owes_data.append({
            "Who": member,
            "Owes": paid_by,
            "Amount ($)": share
        })

if not owes_data:
    st.success("🎉 No debts found — everyone paid for themselves!")
    st.stop()

owes_df = pd.DataFrame(owes_data)

# group and sum
summary = owes_df.groupby(["Who", "Owes"])["Amount ($)"].sum().reset_index()
summary["Amount ($)"] = summary["Amount ($)"].round(2)

# subtract existing settlements
settlements_group = settlements_df[settlements_df["Group"] == selected_group]
for _, s in settlements_group.iterrows():
    mask = (summary["Who"] == s["From"]) & (summary["Owes"] == s["To"])
    if mask.any():
        summary.loc[mask, "Amount ($)"] -= s["Amount ($)"]

# remove cleared debts
summary = summary[summary["Amount ($)"] > 0.01]

if summary.empty:
    st.success("🎉 All debts are fully settled!")
else:
    # show each debt with a settle button
    for idx, row in summary.iterrows():

        col1, col2, col3, col4 = st.columns([2, 2, 1, 2])

        with col1:
            st.error(f"👤 **{row['Who']}**")

        with col2:
            st.success(f"💸 owes **{row['Owes']}**")

        with col3:
            st.metric("", f"${row['Amount ($)']:.2f}")

        with col4:
            if st.button(f"✅ Settle", key=f"settle_{idx}"):
                save_settlement(
                    group=selected_group,
                    from_person=row["Who"],
                    to_person=row["Owes"],
                    amount=row["Amount ($)"]
                )
                st.success(f"✅ {row['Who']} settled ${row['Amount ($)']:.2f} with {row['Owes']}!")
                st.rerun()

st.divider()

# --- PARTIAL SETTLEMENT ---
st.subheader("💵 Record a Partial Payment")
st.write("Use this if someone pays only part of what they owe.")

members = groups_df[groups_df["Group"] == selected_group]["Member"].tolist()

col1, col2 = st.columns(2)

with col1:
    from_person = st.selectbox("Who is paying?", members, key="from_person")

with col2:
    to_options = [m for m in members if m != from_person]
    to_person = st.selectbox("Who are they paying?", to_options, key="to_person")

partial_amount = st.number_input(
    "Amount ($)",
    min_value=0.01,
    value=10.0,
    step=0.01
)

if st.button("💾 Record Partial Payment"):
    save_settlement(
        group=selected_group,
        from_person=from_person,
        to_person=to_person,
        amount=partial_amount
    )
    st.success(f"✅ Recorded: {from_person} paid ${partial_amount:.2f} to {to_person}!")
    st.rerun()

st.divider()

# --- SETTLEMENT HISTORY ---
st.subheader("📜 Settlement History")

if settlements_group.empty:
    st.info("No settlements recorded yet for this group.")
else:
    st.dataframe(settlements_group, use_container_width=True)

    total_settled = settlements_group["Amount ($)"].sum()
    st.metric("💰 Total Settled", f"${total_settled:.2f}")

    st.divider()

    # --- SETTLEMENT CHART ---
    st.subheader("📊 Settlement Chart")

    fig = px.bar(
        settlements_group,
        x="From",
        y="Amount ($)",
        color="To",
        title="Settlements by person",
        text="Amount ($)",
        barmode="group"
    )

    fig.update_traces(texttemplate="$%{text:.2f}", textposition="outside")
    fig.update_layout(yaxis_range=[0, settlements_group["Amount ($)"].max() * 1.4])

    st.plotly_chart(fig, use_container_width=True)