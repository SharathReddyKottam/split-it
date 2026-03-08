import streamlit as st
import pandas as pd
import plotly.express as px
from utils.file_helpers import load_groups, load_expenses, load_settlements

# --- PAGE CONFIG ---
st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")

st.title("📊 Spending Dashboard")
st.write("Deep insights into your group spending.")

st.divider()

# --- LOAD DATA ---
groups_df = load_groups()
expenses_df = load_expenses()
settlements_df = load_settlements()

if expenses_df.empty:
    st.warning("⚠️ No expenses found. Add some expenses first!")
    st.stop()

# --- FILTERS ---
st.subheader("🔍 Filters")

col1, col2, col3 = st.columns(3)

with col1:
    group_options = ["All Groups"] + groups_df["Group"].unique().tolist()
    selected_group = st.selectbox("Group", group_options)

with col2:
    category_options = ["All Categories"] + expenses_df["Category"].unique().tolist()
    selected_category = st.selectbox("Category", category_options)

with col3:
    member_options = ["All Members"] + expenses_df["Member"].unique().tolist()
    selected_member = st.selectbox("Member", member_options)

# --- APPLY FILTERS ---
filtered_df = expenses_df.copy()

if selected_group != "All Groups":
    filtered_df = filtered_df[filtered_df["Group"] == selected_group]

if selected_category != "All Categories":
    filtered_df = filtered_df[filtered_df["Category"] == selected_category]

if selected_member != "All Members":
    filtered_df = filtered_df[filtered_df["Member"] == selected_member]

if filtered_df.empty:
    st.info("No expenses match your filters.")
    st.stop()

st.divider()

# --- TOP METRICS ---
st.subheader("📈 Overview")

# get unique expenses to avoid double counting
unique_expenses = filtered_df.drop_duplicates(subset="ExpenseID")

total_spent = unique_expenses["Amount ($)"].sum()
num_expenses = unique_expenses["ExpenseID"].nunique()
avg_expense = total_spent / num_expenses if num_expenses > 0 else 0
biggest_expense = unique_expenses["Amount ($)"].max()

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("💰 Total Spent", f"${total_spent:.2f}")

with col2:
    st.metric("🧾 No. of Expenses", num_expenses)

with col3:
    st.metric("📊 Avg per Expense", f"${avg_expense:.2f}")

with col4:
    st.metric("🔝 Biggest Expense", f"${biggest_expense:.2f}")

st.divider()

# --- ROW 1: CATEGORY + MEMBER CHARTS ---
st.subheader("📊 Spending Breakdown")

col1, col2 = st.columns(2)

with col1:
    # spending by category
    category_df = unique_expenses.groupby("Category")["Amount ($)"].sum().reset_index()
    category_df = category_df.sort_values("Amount ($)", ascending=False)

    fig1 = px.pie(
        category_df,
        names="Category",
        values="Amount ($)",
        title="Spending by Category",
        hole=0.4
    )
    fig1.update_traces(textposition="inside", textinfo="percent+label")
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    # spending by member
    member_df = filtered_df.groupby("Member")["Share ($)"].sum().reset_index()
    member_df = member_df.sort_values("Share ($)", ascending=False)
    member_df.rename(columns={"Share ($)": "Total Owed ($)"}, inplace=True)

    fig2 = px.bar(
        member_df,
        x="Member",
        y="Total Owed ($)",
        color="Member",
        title="Total Owed per Person",
        text="Total Owed ($)"
    )
    fig2.update_traces(texttemplate="$%{text:.2f}", textposition="outside")
    fig2.update_layout(
        showlegend=False,
        yaxis_range=[0, member_df["Total Owed ($)"].max() * 1.3]
    )
    st.plotly_chart(fig2, use_container_width=True)

st.divider()

# --- ROW 2: SPENDING OVER TIME ---
st.subheader("📅 Spending Over Time")

# convert date column to datetime
unique_expenses["Date"] = pd.to_datetime(unique_expenses["Date"])

# group by date
time_df = unique_expenses.groupby(
    unique_expenses["Date"].dt.date
)["Amount ($)"].sum().reset_index()
time_df.columns = ["Date", "Amount ($)"]
time_df = time_df.sort_values("Date")

fig3 = px.line(
    time_df,
    x="Date",
    y="Amount ($)",
    title="Total Spending Over Time",
    markers=True
)
fig3.update_layout(yaxis_range=[0, time_df["Amount ($)"].max() * 1.3])
st.plotly_chart(fig3, use_container_width=True)

st.divider()

# --- ROW 3: SPENDING BY GROUP + CATEGORY HEATMAP ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("👥 Spending by Group")

    group_df = unique_expenses.groupby("Group")["Amount ($)"].sum().reset_index()
    group_df = group_df.sort_values("Amount ($)", ascending=True)

    fig4 = px.bar(
        group_df,
        x="Amount ($)",
        y="Group",
        orientation="h",
        color="Group",
        title="Total Spent per Group",
        text="Amount ($)"
    )
    fig4.update_traces(texttemplate="$%{text:.2f}", textposition="outside")
    fig4.update_layout(showlegend=False)
    st.plotly_chart(fig4, use_container_width=True)

with col2:
    st.subheader("🔥 Category vs Member Heatmap")

    # pivot table: members as rows, categories as columns
    heatmap_df = filtered_df.groupby(
        ["Member", "Category"]
    )["Share ($)"].sum().reset_index()

    heatmap_pivot = heatmap_df.pivot(
        index="Member",
        columns="Category",
        values="Share ($)"
    ).fillna(0)

    fig5 = px.imshow(
        heatmap_pivot,
        title="Spending Heatmap (Member vs Category)",
        color_continuous_scale="Blues",
        text_auto=".2f"
    )
    st.plotly_chart(fig5, use_container_width=True)

st.divider()

# --- FULL EXPENSE TABLE ---
st.subheader("📋 Full Expense Log")

display_cols = ["Date", "Group", "Expense", "Category", "Paid By", "Amount ($)"]
unique_display = filtered_df.drop_duplicates(subset="ExpenseID")[display_cols]
unique_display = unique_display.sort_values("Date", ascending=False)

st.dataframe(unique_display, use_container_width=True)