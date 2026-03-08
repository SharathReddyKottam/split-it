import streamlit as st
import pandas as pd
import plotly.express as px
import calplot
import matplotlib.pyplot as plt
from utils.file_helpers import load_groups, load_expenses

# --- PAGE CONFIG ---
st.set_page_config(page_title="Expense Heatmap", page_icon="🗓️", layout="wide")

st.title("🗓️ Expense Heatmap")
st.write("See which days and months you spend the most.")

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
unique_expenses["Day"] = unique_expenses["Date"].dt.date
unique_expenses["Week"] = unique_expenses["Date"].dt.isocalendar().week.astype(int)
unique_expenses["Weekday"] = unique_expenses["Date"].dt.day_name()
unique_expenses["Month"] = unique_expenses["Date"].dt.strftime("%b %Y")
unique_expenses["Month Num"] = unique_expenses["Date"].dt.to_period("M").astype(str)
unique_expenses["Hour"] = unique_expenses["Date"].dt.hour

# --- FILTERS ---
st.subheader("🔍 Filters")

col1, col2 = st.columns(2)

with col1:
    group_options = ["All Groups"] + groups_df["Group"].unique().tolist()
    selected_group = st.selectbox("Group", group_options)

with col2:
    category_options = ["All Categories"] + unique_expenses["Category"].unique().tolist()
    selected_category = st.selectbox("Category", category_options)

# --- APPLY FILTERS ---
filtered_df = unique_expenses.copy()

if selected_group != "All Groups":
    filtered_df = filtered_df[filtered_df["Group"] == selected_group]

if selected_category != "All Categories":
    filtered_df = filtered_df[filtered_df["Category"] == selected_category]

if filtered_df.empty:
    st.info("No expenses match your filters.")
    st.stop()

st.divider()

# --- CALENDAR HEATMAP ---
st.subheader("📅 Calendar Heatmap")
st.write("Each square is one day — darker means more spending.")

# group spending by day
daily_spending = filtered_df.groupby("Day")["Amount ($)"].sum()
daily_spending.index = pd.to_datetime(daily_spending.index)

# plot calendar heatmap
fig_cal, ax = calplot.calplot(
    daily_spending,
    cmap="YlOrRd",
    colorbar=True,
    suptitle="Daily Spending Heatmap"
)

st.pyplot(fig_cal)

st.divider()

# --- ROW 1: DAY OF WEEK + MONTH ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("📊 Spending by Day of Week")

    # order days correctly
    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    dow_df = filtered_df.groupby("Weekday")["Amount ($)"].sum().reset_index()
    dow_df.columns = ["Day", "Amount ($)"]
    dow_df["Day"] = pd.Categorical(dow_df["Day"], categories=day_order, ordered=True)
    dow_df = dow_df.sort_values("Day")

    fig1 = px.bar(
        dow_df,
        x="Day",
        y="Amount ($)",
        color="Amount ($)",
        color_continuous_scale="YlOrRd",
        title="Which day do you spend most?",
        text="Amount ($)"
    )
    fig1.update_traces(texttemplate="$%{text:.2f}", textposition="outside")
    fig1.update_layout(
        showlegend=False,
        yaxis_range=[0, dow_df["Amount ($)"].max() * 1.3]
    )
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    st.subheader("📅 Spending by Month")

    month_df = filtered_df.groupby(
        ["Month Num", "Month"]
    )["Amount ($)"].sum().reset_index()
    month_df = month_df.sort_values("Month Num")

    fig2 = px.bar(
        month_df,
        x="Month",
        y="Amount ($)",
        color="Amount ($)",
        color_continuous_scale="YlOrRd",
        title="Which month do you spend most?",
        text="Amount ($)"
    )
    fig2.update_traces(texttemplate="$%{text:.2f}", textposition="outside")
    fig2.update_layout(
        showlegend=False,
        yaxis_range=[0, month_df["Amount ($)"].max() * 1.3]
    )
    st.plotly_chart(fig2, use_container_width=True)

st.divider()

# --- ROW 2: WEEKLY SPENDING + BUBBLE CHART ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("📆 Weekly Spending")

    weekly_df = filtered_df.groupby("Week")["Amount ($)"].sum().reset_index()
    weekly_df.columns = ["Week Number", "Amount ($)"]
    weekly_df = weekly_df.sort_values("Week Number")

    fig3 = px.area(
        weekly_df,
        x="Week Number",
        y="Amount ($)",
        title="Spending per Week Number",
        markers=True
    )
    fig3.update_layout(yaxis_range=[0, weekly_df["Amount ($)"].max() * 1.3])
    st.plotly_chart(fig3, use_container_width=True)

with col2:
    st.subheader("🫧 Spending Bubble Chart")

    bubble_df = filtered_df.groupby(
        ["Day", "Category"]
    )["Amount ($)"].sum().reset_index()
    bubble_df["Day"] = pd.to_datetime(bubble_df["Day"])

    fig4 = px.scatter(
        bubble_df,
        x="Day",
        y="Category",
        size="Amount ($)",
        color="Category",
        title="Spending Bubbles by Category Over Time",
        hover_data=["Amount ($)"]
    )
    fig4.update_layout(showlegend=False)
    st.plotly_chart(fig4, use_container_width=True)

st.divider()

# --- DAILY SPENDING TABLE ---
st.subheader("📋 Daily Spending Log")

daily_log = filtered_df.groupby("Day").agg(
    Total_Spent=("Amount ($)", "sum"),
    Num_Expenses=("ExpenseID", "nunique"),
    Categories=("Category", lambda x: ", ".join(x.unique()))
).reset_index()

daily_log.columns = ["Date", "Total Spent ($)", "No. of Expenses", "Categories"]
daily_log = daily_log.sort_values("Date", ascending=False)
daily_log["Total Spent ($)"] = daily_log["Total Spent ($)"].round(2)

st.dataframe(daily_log, use_container_width=True)