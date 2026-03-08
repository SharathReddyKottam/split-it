import streamlit as st
import pandas as pd
import plotly.express as px
from utils.file_helpers import load_groups, load_expenses

# --- PAGE CONFIG ---
st.set_page_config(page_title="Search & Filter", page_icon="🔍", layout="wide")

st.title("🔍 Search & Filter")
st.write("Find any expense instantly across all your groups.")

st.divider()

# --- LOAD DATA ---
expenses_df = load_expenses()
groups_df = load_groups()

if expenses_df.empty:
    st.warning("⚠️ No expenses found. Add some expenses first!")
    st.stop()

# --- PREPARE DATA ---
unique_expenses = expenses_df.drop_duplicates(subset="ExpenseID").copy()
unique_expenses["Date"] = pd.to_datetime(unique_expenses["Date"])

st.subheader("🔍 Search & Filters")

# --- ROW 1: TEXT SEARCH + GROUP ---
col1, col2 = st.columns(2)

with col1:
    search_query = st.text_input("🔎 Search by expense name", placeholder="e.g. Pizza, Uber...")

with col2:
    group_options = ["All Groups"] + groups_df["Group"].unique().tolist()
    selected_group = st.selectbox("👥 Group", group_options)

# --- ROW 2: CATEGORY + PAID BY ---
col1, col2 = st.columns(2)

with col1:
    category_options = ["All Categories"] + unique_expenses["Category"].unique().tolist()
    selected_category = st.selectbox("🏷️ Category", category_options)

with col2:
    member_options = ["All Members"] + unique_expenses["Paid By"].unique().tolist()
    selected_paid_by = st.selectbox("💳 Paid By", member_options)

# --- ROW 3: AMOUNT RANGE + DATE RANGE ---
col1, col2 = st.columns(2)

with col1:
    min_amount = float(unique_expenses["Amount ($)"].min())
    max_amount = float(unique_expenses["Amount ($)"].max())

    amount_range = st.slider(
        "💰 Amount Range ($)",
        min_value=min_amount,
        max_value=max_amount,
        value=(min_amount, max_amount)
    )

with col2:
    min_date = unique_expenses["Date"].min().date()
    max_date = unique_expenses["Date"].max().date()

    date_range = st.date_input(
        "📅 Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

# --- ROW 4: SPLIT TYPE ---
split_options = ["All"] + unique_expenses["Split Type"].unique().tolist()
selected_split = st.selectbox("⚖️ Split Type", split_options)

st.divider()

# --- APPLY ALL FILTERS ---
filtered_df = unique_expenses.copy()

# text search
if search_query:
    filtered_df = filtered_df[
        filtered_df["Expense"].str.contains(search_query, case=False, na=False)
    ]

# group filter
if selected_group != "All Groups":
    filtered_df = filtered_df[filtered_df["Group"] == selected_group]

# category filter
if selected_category != "All Categories":
    filtered_df = filtered_df[filtered_df["Category"] == selected_category]

# paid by filter
if selected_paid_by != "All Members":
    filtered_df = filtered_df[filtered_df["Paid By"] == selected_paid_by]

# amount range filter
filtered_df = filtered_df[
    (filtered_df["Amount ($)"] >= amount_range[0]) &
    (filtered_df["Amount ($)"] <= amount_range[1])
    ]

# date range filter
if len(date_range) == 2:
    filtered_df = filtered_df[
        (filtered_df["Date"].dt.date >= date_range[0]) &
        (filtered_df["Date"].dt.date <= date_range[1])
        ]

# split type filter
if selected_split != "All":
    filtered_df = filtered_df[filtered_df["Split Type"] == selected_split]

st.divider()

# --- RESULTS HEADER ---
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("🔍 Results Found", len(filtered_df))

with col2:
    total = filtered_df["Amount ($)"].sum()
    st.metric("💰 Total Amount", f"${total:.2f}")

with col3:
    avg = filtered_df["Amount ($)"].mean() if len(filtered_df) > 0 else 0
    st.metric("📊 Average Amount", f"${avg:.2f}")

with col4:
    if len(filtered_df) > 0:
        top_category = filtered_df["Category"].value_counts().idxmax()
    else:
        top_category = "N/A"
    st.metric("🏷️ Top Category", top_category)

st.divider()

if filtered_df.empty:
    st.info("No expenses match your filters. Try adjusting them above!")
    st.stop()

# --- RESULTS TABLE ---
st.subheader(f"📋 Results ({len(filtered_df)} expenses)")

# sort options
sort_col, sort_order_col = st.columns(2)

with sort_col:
    sort_by = st.selectbox("Sort by", ["Date", "Amount ($)", "Expense", "Category", "Group"])

with sort_order_col:
    sort_order = st.radio("Order", ["Descending", "Ascending"], horizontal=True)

ascending = sort_order == "Ascending"
filtered_df = filtered_df.sort_values(sort_by, ascending=ascending)

# display results
display_cols = ["Date", "Group", "Expense", "Category", "Paid By", "Amount ($)", "Split Type"]
st.dataframe(
    filtered_df[display_cols].reset_index(drop=True),
    use_container_width=True
)

st.divider()

# --- CHARTS FOR SEARCH RESULTS ---
st.subheader("📊 Visual Breakdown of Results")

col1, col2 = st.columns(2)

with col1:
    # category breakdown of results
    cat_df = filtered_df.groupby("Category")["Amount ($)"].sum().reset_index()
    cat_df = cat_df.sort_values("Amount ($)", ascending=False)

    fig1 = px.pie(
        cat_df,
        names="Category",
        values="Amount ($)",
        title="Results by Category",
        hole=0.4
    )
    fig1.update_traces(textposition="inside", textinfo="percent+label")
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    # spending over time for results
    time_df = filtered_df.groupby(
        filtered_df["Date"].dt.date
    )["Amount ($)"].sum().reset_index()
    time_df.columns = ["Date", "Amount ($)"]
    time_df = time_df.sort_values("Date")

    fig2 = px.line(
        time_df,
        x="Date",
        y="Amount ($)",
        title="Results Over Time",
        markers=True
    )
    st.plotly_chart(fig2, use_container_width=True)

st.divider()

# --- DOWNLOAD RESULTS ---
st.subheader("⬇️ Download Results")

csv = filtered_df[display_cols].to_csv(index=False).encode("utf-8")

st.download_button(
    label="⬇️ Download filtered results as CSV",
    data=csv,
    file_name="search_results.csv",
    mime="text/csv"
)