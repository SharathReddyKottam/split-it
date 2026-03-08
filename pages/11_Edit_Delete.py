import streamlit as st
import pandas as pd
from datetime import datetime
from utils.file_helpers import load_groups, load_expenses, save_expenses, delete_expense

# --- PAGE CONFIG ---
st.set_page_config(page_title="Edit & Delete", page_icon="✏️", layout="wide")

st.title("✏️ Edit & Delete Expenses")
st.write("Fix mistakes or remove expenses from your groups.")

st.divider()

# --- LOAD DATA ---
expenses_df = load_expenses()
groups_df = load_groups()

if expenses_df.empty:
    st.warning("⚠️ No expenses found. Add some expenses first!")
    st.stop()

# --- FILTERS ---
st.subheader("🔍 Find an Expense")

col1, col2 = st.columns(2)

with col1:
    group_options = ["All Groups"] + groups_df["Group"].unique().tolist()
    selected_group = st.selectbox("Group", group_options)

with col2:
    search_query = st.text_input("Search by name", placeholder="e.g. Pizza, Uber...")

# --- APPLY FILTERS ---
unique_expenses = expenses_df.drop_duplicates(subset="ExpenseID").copy()

if selected_group != "All Groups":
    unique_expenses = unique_expenses[unique_expenses["Group"] == selected_group]

if search_query:
    unique_expenses = unique_expenses[
        unique_expenses["Expense"].str.contains(search_query, case=False, na=False)
    ]

if unique_expenses.empty:
    st.info("No expenses match your filters.")
    st.stop()

st.divider()

# --- EXPENSE LIST ---
st.subheader("📋 Select an Expense to Edit or Delete")

# build a readable label for each expense
unique_expenses["Label"] = (
        unique_expenses["Date"] + " | " +
        unique_expenses["Expense"] + " | $" +
        unique_expenses["Amount ($)"].astype(str) + " | " +
        unique_expenses["Group"]
)

selected_label = st.selectbox("Select expense", unique_expenses["Label"].tolist())

# get the selected expense row
selected_row = unique_expenses[unique_expenses["Label"] == selected_label].iloc[0]
selected_id = selected_row["ExpenseID"]

# get all rows for this expense (one per member)
all_rows = expenses_df[expenses_df["ExpenseID"] == selected_id].copy()
members_in_expense = all_rows["Member"].tolist()

st.divider()

# --- SHOW CURRENT DETAILS ---
st.subheader("📄 Current Details")

col1, col2, col3 = st.columns(3)
with col1:
    st.info(f"**Expense:** {selected_row['Expense']}")
    st.info(f"**Group:** {selected_row['Group']}")
with col2:
    st.info(f"**Amount:** ${selected_row['Amount ($)']}")
    st.info(f"**Paid By:** {selected_row['Paid By']}")
with col3:
    st.info(f"**Category:** {selected_row['Category']}")
    st.info(f"**Date:** {selected_row['Date']}")

st.write("**Members involved:**", ", ".join(members_in_expense))

st.divider()

# --- TWO TABS: EDIT AND DELETE ---
tab1, tab2 = st.tabs(["✏️ Edit Expense", "🗑️ Delete Expense"])

# =====================
# TAB 1 — EDIT
# =====================
with tab1:
    st.subheader("✏️ Edit Expense Details")

    col1, col2 = st.columns(2)

    with col1:
        new_name = st.text_input("Expense name", value=selected_row["Expense"])

        new_category = st.selectbox("Category", [
            "🍕 Food & Drink",
            "🚗 Transport",
            "🏠 Rent & Utilities",
            "🎬 Entertainment",
            "🛒 Groceries",
            "✈️ Travel",
            "💊 Health",
            "📦 Other"
        ], index=[
            "🍕 Food & Drink",
            "🚗 Transport",
            "🏠 Rent & Utilities",
            "🎬 Entertainment",
            "🛒 Groceries",
            "✈️ Travel",
            "💊 Health",
            "📦 Other"
        ].index(selected_row["Category"]) if selected_row["Category"] in [
            "🍕 Food & Drink",
            "🚗 Transport",
            "🏠 Rent & Utilities",
            "🎬 Entertainment",
            "🛒 Groceries",
            "✈️ Travel",
            "💊 Health",
            "📦 Other"
        ] else 0)

    with col2:
        new_amount = st.number_input(
            "Total amount ($)",
            min_value=0.0,
            value=float(selected_row["Amount ($)"]),
            step=0.01
        )

        # get group members for paid by
        group_members = groups_df[
            groups_df["Group"] == selected_row["Group"]
            ]["Member"].tolist()

        new_paid_by = st.selectbox(
            "Paid by",
            group_members,
            index=group_members.index(selected_row["Paid By"])
            if selected_row["Paid By"] in group_members else 0
        )

    st.write("**Members involved in this expense:**")

    # checkboxes for members
    all_group_members = groups_df[
        groups_df["Group"] == selected_row["Group"]
        ]["Member"].tolist()

    new_members = []
    check_cols = st.columns(4)
    for i, member in enumerate(all_group_members):
        with check_cols[i % 4]:
            checked = member in members_in_expense
            if st.checkbox(member, value=checked, key=f"edit_{member}"):
                new_members.append(member)

    if len(new_members) == 0:
        st.error("❌ Please select at least one member!")
    else:
        new_share = round(new_amount / len(new_members), 2)
        st.info(f"New share per person: **${new_share:.2f}**")

        if st.button("💾 Save Changes", type="primary"):

            # delete old expense rows
            updated_df = expenses_df[expenses_df["ExpenseID"] != selected_id].copy()

            # build new rows with updated details
            timestamp = selected_row["Date"]
            new_rows = []
            for member in new_members:
                new_rows.append({
                    "ExpenseID": selected_id,
                    "Date": timestamp,
                    "Group": selected_row["Group"],
                    "Expense": new_name,
                    "Category": new_category,
                    "Paid By": new_paid_by,
                    "Amount ($)": new_amount,
                    "Split Type": "Equal split",
                    "Member": member,
                    "Share ($)": new_share
                })

            new_rows_df = pd.DataFrame(new_rows)
            final_df = pd.concat([updated_df, new_rows_df], ignore_index=True)
            final_df.to_csv("data/expenses.csv", index=False)

            st.success(f"✅ Expense '{new_name}' updated successfully!")
            st.rerun()

# =====================
# TAB 2 — DELETE
# =====================
with tab2:
    st.subheader("🗑️ Delete Expense")

    st.warning(f"⚠️ You are about to delete **'{selected_row['Expense']}'** — this cannot be undone!")

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Expense", selected_row["Expense"])
    with col2:
        st.metric("Amount", f"${selected_row['Amount ($)']:.2f}")

    # safety confirmation checkbox
    confirm = st.checkbox("Yes I am sure, delete this expense permanently")

    if confirm:
        if st.button("🗑️ Delete Expense", type="primary"):
            updated_df = expenses_df[expenses_df["ExpenseID"] != selected_id].copy()
            updated_df.to_csv("data/expenses.csv", index=False)
            st.success("✅ Expense deleted successfully!")
            st.rerun()