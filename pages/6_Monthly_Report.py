import streamlit as st
import pandas as pd
import plotly.express as px
from utils.file_helpers import load_groups, load_expenses

# --- PAGE CONFIG ---
st.set_page_config(page_title="Monthly Report", page_icon="📅", layout="wide")

st.title("📅 Monthly Report")
st.write("Track how your spending changes month by month.")

st.divider()

# --- LOAD DATA ---
expenses_df = load_expenses()

if expenses_df.empty:
    st.warning("⚠️ No expenses found. Add some expenses first!")
    st.stop()

# --- PREPARE DATES ---
unique_expenses = expenses_df.drop_duplicates(subset="ExpenseID").copy()
unique_expenses["Date"] = pd.to_datetime(unique_expenses["Date"])
unique_expenses["Month"] = unique_expenses["Date"].dt.to_period("M").astype(str)
unique_expenses["Month Name"] = unique_expenses["Date"].dt.strftime("%b %Y")

# --- FILTERS ---
st.subheader("🔍 Filters")

col1, col2 = st.columns(2)

with col1:
    groups_df = load_groups()
    group_options = ["All Groups"] + groups_df["Group"].unique().tolist()
    selected_group = st.selectbox("Group", group_options)

with col2:
    all_months = sorted(unique_expenses["Month"].unique().tolist())
    selected_months = st.multiselect(
        "Filter by months",
        options=all_months,
        default=all_months
    )

# --- APPLY FILTERS ---
filtered_df = unique_expenses.copy()

if selected_group != "All Groups":
    filtered_df = filtered_df[filtered_df["Group"] == selected_group]

if selected_months:
    filtered_df = filtered_df[filtered_df["Month"].isin(selected_months)]

if filtered_df.empty:
    st.info("No expenses match your filters.")
    st.stop()

st.divider()

# --- MONTHLY SUMMARY ---
monthly_df = filtered_df.groupby(
    ["Month", "Month Name"]
)["Amount ($)"].sum().reset_index()
monthly_df = monthly_df.sort_values("Month")

# --- TOP METRICS ---
st.subheader("📈 Overview")

col1, col2, col3, col4 = st.columns(4)

with col1:
    total = filtered_df["Amount ($)"].sum()
    st.metric("💰 Total Spent", f"${total:.2f}")

with col2:
    avg_monthly = monthly_df["Amount ($)"].mean()
    st.metric("📊 Avg per Month", f"${avg_monthly:.2f}")

with col3:
    busiest_month = monthly_df.loc[monthly_df["Amount ($)"].idxmax(), "Month Name"]
    st.metric("🔝 Busiest Month", busiest_month)

with col4:
    quietest_month = monthly_df.loc[monthly_df["Amount ($)"].idxmin(), "Month Name"]
    st.metric("💤 Quietest Month", quietest_month)

st.divider()

# --- ROW 1: BAR + LINE CHARTS ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("📊 Monthly Spending Bar Chart")

    fig1 = px.bar(
        monthly_df,
        x="Month Name",
        y="Amount ($)",
        color="Amount ($)",
        color_continuous_scale="Blues",
        title="Total Spending per Month",
        text="Amount ($)"
    )
    fig1.update_traces(texttemplate="$%{text:.2f}", textposition="outside")
    fig1.update_layout(
        showlegend=False,
        yaxis_range=[0, monthly_df["Amount ($)"].max() * 1.3]
    )
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    st.subheader("📈 Spending Trend")

    fig2 = px.line(
        monthly_df,
        x="Month Name",
        y="Amount ($)",
        title="Spending Trend Over Months",
        markers=True
    )

    # add average line
    avg = monthly_df["Amount ($)"].mean()
    fig2.add_hline(
        y=avg,
        line_dash="dash",
        line_color="red",
        annotation_text=f"Avg: ${avg:.2f}",
        annotation_position="top right"
    )
    fig2.update_layout(yaxis_range=[0, monthly_df["Amount ($)"].max() * 1.3])
    st.plotly_chart(fig2, use_container_width=True)

st.divider()

# --- ROW 2: CATEGORY BREAKDOWN BY MONTH ---
st.subheader("🍕 Category Breakdown by Month")

# merge month info back into full filtered expenses
full_filtered = expenses_df.copy()
full_filtered["Date"] = pd.to_datetime(full_filtered["Date"])
full_filtered["Month"] = full_filtered["Date"].dt.to_period("M").astype(str)
full_filtered["Month Name"] = full_filtered["Date"].dt.strftime("%b %Y")

if selected_group != "All Groups":
    full_filtered = full_filtered[full_filtered["Group"] == selected_group]
if selected_months:
    full_filtered = full_filtered[full_filtered["Month"].isin(selected_months)]

# drop duplicates to get unique expenses
unique_full = full_filtered.drop_duplicates(subset="ExpenseID")

category_month_df = unique_full.groupby(
    ["Month Name", "Category"]
)["Amount ($)"].sum().reset_index()

fig3 = px.bar(
    category_month_df,
    x="Month Name",
    y="Amount ($)",
    color="Category",
    title="Spending by Category per Month",
    barmode="stack",
    text="Amount ($)"
)
fig3.update_traces(texttemplate="$%{text:.2f}", textposition="inside")
st.plotly_chart(fig3, use_container_width=True)

st.divider()

# --- ROW 3: MONTH ON MONTH CHANGE ---
st.subheader("📉 Month on Month Change")

monthly_df["Prev Month ($)"] = monthly_df["Amount ($)"].shift(1)
monthly_df["Change ($)"] = monthly_df["Amount ($)"] - monthly_df["Prev Month ($)"]
monthly_df["Change (%)"] = (
        (monthly_df["Change ($)"] / monthly_df["Prev Month ($)"]) * 100
).round(1)

# drop first month as it has no previous month
change_df = monthly_df.dropna(subset=["Change ($)"])

if change_df.empty:
    st.info("Need at least 2 months of data to show changes.")
else:
    fig4 = px.bar(
        change_df,
        x="Month Name",
        y="Change ($)",
        color="Change ($)",
        color_continuous_scale=["red", "lightgray", "green"],
        title="Month on Month Spending Change ($)",
        text="Change ($)"
    )
    fig4.update_traces(texttemplate="$%{text:.2f}", textposition="outside")
    fig4.update_layout(
        showlegend=False,
        yaxis_range=[
            change_df["Change ($)"].min() * 1.4,
            change_df["Change ($)"].max() * 1.4
        ]
    )
    st.plotly_chart(fig4, use_container_width=True)

st.divider()

# --- MONTHLY SUMMARY TABLE ---
st.subheader("📋 Monthly Summary Table")

display_df = monthly_df[["Month Name", "Amount ($)", "Change ($)", "Change (%)"]].copy()
display_df["Amount ($)"] = display_df["Amount ($)"].round(2)
display_df = display_df.fillna("-")

st.dataframe(display_df, use_container_width=True)

st.divider()

# --- DOWNLOAD REPORT ---
st.subheader("⬇️ Download Monthly Report")

csv = display_df.to_csv(index=False).encode("utf-8")

st.download_button(
    label="⬇️ Download as CSV",
    data=csv,
    file_name="monthly_report.csv",
    mime="text/csv"
)