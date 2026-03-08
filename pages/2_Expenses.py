import streamlit as st
import pandas as pd
from datetime import datetime
from utils.file_helpers import load_groups, load_expenses, save_expenses

# --- PAGE CONFIG ---
st.set_page_config(page_title="Expenses", page_icon="🧾", layout="centered")

st.title("🧾 Expenses")
st.write("Add and view expenses for your groups.")

st.divider()

# --- LOAD GROUPS ---
groups_df = load_groups()

if groups_df.empty:
    st.warning("⚠️ No groups found. Please create a group first!")
    st.stop()

# --- SELECT GROUP ---
group_names = groups_df["Group"].unique().tolist()
selected_group = st.selectbox("Select a group", group_names)

# get ALL members of selected group
all_members = groups_df[groups_df["Group"] == selected_group]["Member"].tolist()

st.divider()

# --- ADD EXPENSE ---
st.subheader("➕ Add an Expense")

expense_name = st.text_input("Expense name (e.g. 'Dinner', 'Uber')")

col1, col2 = st.columns(2)

with col1:
    category = st.selectbox("Category", [
        "🍕 Food & Drink",
        "🚗 Transport",
        "🏠 Rent & Utilities",
        "🎬 Entertainment",
        "🛒 Groceries",
        "✈️ Travel",
        "💊 Health",
        "📦 Other"
    ])

with col2:
    paid_by = st.selectbox("Paid by", all_members)

total_amount = st.number_input("Total amount ($)", min_value=0.0, value=50.0, step=0.01)

st.divider()

# --- MEMBER SELECTION ---
st.subheader("👥 Who is involved in this expense?")
st.write("Check the people splitting this transaction:")

selected_members = []

# show members in rows of 4 checkboxes
cols = st.columns(4)
for i, member in enumerate(all_members):
    with cols[i % 4]:
        if st.checkbox(member, value=True, key=f"member_{member}"):
            selected_members.append(member)

# validation
if len(selected_members) == 0:
    st.error("❌ Please select at least one member!")
    st.stop()

st.success(f"✅ Splitting among {len(selected_members)} people: {', '.join(selected_members)}")

st.divider()

# --- SPLIT TYPE ---
st.subheader("⚖️ How to split?")

split_type = st.radio(
    "Split type",
    ["Equal split", "Split by percentage", "Split by exact amount"],
    horizontal=True
)

st.write("")

shares = {}

# --- EQUAL SPLIT ---
if split_type == "Equal split":
    share_per_person = total_amount / len(selected_members)
    st.info(f"Each person pays: **${share_per_person:.2f}**")
    for member in selected_members:
        shares[member] = round(share_per_person, 2)

# --- SPLIT BY PERCENTAGE ---
elif split_type == "Split by percentage":
    st.write("Enter percentage for each person (must add up to 100%):")
    total_percent = 0
    for member in selected_members:
        pct = st.number_input(f"{member} (%)", min_value=0.0, max_value=100.0,
                              value=round(100 / len(selected_members), 2),
                              key=f"pct_{member}")
        shares[member] = round((pct / 100) * total_amount, 2)
        total_percent += pct

    if round(total_percent, 1) != 100.0:
        st.warning(f"⚠️ Percentages add up to {total_percent:.1f}% — must be exactly 100%")
    else:
        st.success("✅ Percentages add up to 100%!")

# --- SPLIT BY EXACT AMOUNT ---
elif split_type == "Split by exact amount":
    st.write("Enter exact amount for each person:")
    total_entered = 0
    for member in selected_members:
        amt = st.number_input(f"{member} ($)", min_value=0.0,
                              value=round(total_amount / len(selected_members), 2),
                              key=f"amt_{member}")
        shares[member] = round(amt, 2)
        total_entered += amt

    difference = round(abs(total_entered - total_amount), 2)
    if difference > 0:
        st.warning(f"⚠️ Amounts add up to ${total_entered:.2f} — should be ${total_amount:.2f} (difference: ${difference:.2f})")
    else:
        st.success("✅ Amounts add up correctly!")

st.divider()

# --- PREVIEW ---
st.subheader("👀 Preview")

preview_data = {
    "Member": list(shares.keys()),
    "Share ($)": list(shares.values())
}
preview_df = pd.DataFrame(preview_data)
st.dataframe(preview_df, use_container_width=True)

st.divider()

# --- SAVE EXPENSE ---
if st.button("💾 Save Expense"):
    if expense_name.strip() == "":
        st.error("❌ Please enter an expense name!")

    elif split_type == "Split by percentage" and round(total_percent, 1) != 100.0:
        st.error("❌ Percentages must add up to 100% before saving!")

    elif split_type == "Split by exact amount" and round(abs(sum(shares.values()) - total_amount), 2) > 0:
        st.error("❌ Amounts must add up to total before saving!")

    else:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        expense_id = f"{timestamp}_{expense_name}".replace(" ", "_")

        rows = []
        for member, share in shares.items():
            rows.append({
                "ExpenseID": expense_id,
                "Date": timestamp,
                "Group": selected_group,
                "Expense": expense_name,
                "Category": category,
                "Paid By": paid_by,
                "Amount ($)": total_amount,
                "Split Type": split_type,
                "Member": member,
                "Share ($)": share
            })

        new_df = pd.DataFrame(rows)
        save_expenses(new_df)
        st.success(f"✅ Expense '{expense_name}' saved!")

st.divider()

# --- VIEW EXPENSES ---
st.subheader(f"📋 Expenses for '{selected_group}'")

expenses_df = load_expenses()
group_expenses = expenses_df[expenses_df["Group"] == selected_group]

if group_expenses.empty:
    st.info("No expenses yet for this group. Add one above!")
else:
    summary = group_expenses.drop_duplicates(subset="ExpenseID")[
        ["Date", "Expense", "Category", "Paid By", "Amount ($)", "Split Type"]
    ]
    st.dataframe(summary, use_container_width=True)

    total = group_expenses.drop_duplicates(subset="ExpenseID")["Amount ($)"].sum()
    st.metric("💰 Total Spent by Group", f"${total:.2f}")