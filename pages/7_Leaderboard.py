import streamlit as st
import pandas as pd
import plotly.express as px
from utils.file_helpers import load_groups, load_expenses, load_settlements

# --- PAGE CONFIG ---
st.set_page_config(page_title="Leaderboard", page_icon="🏆", layout="wide")

st.title("🏆 Leaderboard")
st.write("Rankings, records and fun stats about your group spending.")

st.divider()

# --- LOAD DATA ---
expenses_df = load_expenses()
settlements_df = load_settlements()
groups_df = load_groups()

if expenses_df.empty:
    st.warning("⚠️ No expenses found. Add some expenses first!")
    st.stop()

# --- FILTERS ---
col1, col2 = st.columns(2)

with col1:
    group_options = ["All Groups"] + groups_df["Group"].unique().tolist()
    selected_group = st.selectbox("Group", group_options)

# --- APPLY FILTERS ---
filtered_df = expenses_df.copy()
unique_expenses = expenses_df.drop_duplicates(subset="ExpenseID").copy()

if selected_group != "All Groups":
    filtered_df = filtered_df[filtered_df["Group"] == selected_group]
    unique_expenses = unique_expenses[unique_expenses["Group"] == selected_group]

if filtered_df.empty:
    st.info("No expenses found for this group.")
    st.stop()

st.divider()

# --- RECORD BREAKERS ---
st.subheader("🥇 Record Breakers")

col1, col2, col3, col4 = st.columns(4)

with col1:
    # biggest single spender
    biggest = unique_expenses.loc[unique_expenses["Amount ($)"].idxmax()]
    st.info(f"💸 **Biggest Single Expense**\n\n**{biggest['Expense']}**\n\n${biggest['Amount ($)']:.2f} paid by {biggest['Paid By']}")

with col2:
    # most generous payer
    payer_df = unique_expenses.groupby("Paid By")["Amount ($)"].sum()
    most_generous = payer_df.idxmax()
    st.success(f"🤝 **Most Generous Payer**\n\n**{most_generous}**\n\n${payer_df[most_generous]:.2f} paid in total")

with col3:
    # most active member
    active_df = filtered_df.groupby("Member")["ExpenseID"].nunique()
    most_active = active_df.idxmax()
    st.warning(f"⚡ **Most Active Member**\n\n**{most_active}**\n\n{active_df[most_active]} expenses involved in")

with col4:
    # favourite category
    fav_category = unique_expenses["Category"].value_counts().idxmax()
    fav_count = unique_expenses["Category"].value_counts().max()
    st.error(f"🍕 **Most Popular Category**\n\n**{fav_category}**\n\n{fav_count} expenses")

st.divider()

# --- LEADERBOARD 1: TOTAL PAID ---
st.subheader("💸 Who Paid the Most?")

paid_df = unique_expenses.groupby("Paid By")["Amount ($)"].sum().reset_index()
paid_df.columns = ["Member", "Total Paid ($)"]
paid_df = paid_df.sort_values("Total Paid ($)", ascending=False).reset_index(drop=True)
paid_df.index += 1
paid_df.index.name = "Rank"

col1, col2 = st.columns(2)

with col1:
    # add medal emojis
    def add_medal(rank):
        if rank == 1: return "🥇"
        if rank == 2: return "🥈"
        if rank == 3: return "🥉"
        return f"#{rank}"

    paid_display = paid_df.copy().reset_index()
    paid_display["Rank"] = paid_display["Rank"].apply(add_medal)
    st.dataframe(paid_display, use_container_width=True, hide_index=True)

with col2:
    fig1 = px.bar(
        paid_df.reset_index(),
        x="Member",
        y="Total Paid ($)",
        color="Member",
        title="Total Amount Paid per Person",
        text="Total Paid ($)"
    )
    fig1.update_traces(texttemplate="$%{text:.2f}", textposition="outside")
    fig1.update_layout(
        showlegend=False,
        yaxis_range=[0, paid_df["Total Paid ($)"].max() * 1.3]
    )
    st.plotly_chart(fig1, use_container_width=True)

st.divider()

# --- LEADERBOARD 2: TOTAL OWED ---
st.subheader("💳 Who Owes the Most?")

owed_df = filtered_df.groupby("Member")["Share ($)"].sum().reset_index()
owed_df.columns = ["Member", "Total Owed ($)"]
owed_df = owed_df.sort_values("Total Owed ($)", ascending=False).reset_index(drop=True)
owed_df.index += 1
owed_df.index.name = "Rank"

col1, col2 = st.columns(2)

with col1:
    owed_display = owed_df.copy().reset_index()
    owed_display["Rank"] = owed_display["Rank"].apply(add_medal)
    st.dataframe(owed_display, use_container_width=True, hide_index=True)

with col2:
    fig2 = px.bar(
        owed_df.reset_index(),
        x="Member",
        y="Total Owed ($)",
        color="Member",
        title="Total Amount Owed per Person",
        text="Total Owed ($)"
    )
    fig2.update_traces(texttemplate="$%{text:.2f}", textposition="outside")
    fig2.update_layout(
        showlegend=False,
        yaxis_range=[0, owed_df["Total Owed ($)"].max() * 1.3]
    )
    st.plotly_chart(fig2, use_container_width=True)

st.divider()

# --- LEADERBOARD 3: MOST ACTIVE ---
st.subheader("⚡ Most Active Members")

active_full_df = filtered_df.groupby("Member")["ExpenseID"].nunique().reset_index()
active_full_df.columns = ["Member", "Expenses Involved In"]
active_full_df = active_full_df.sort_values("Expenses Involved In", ascending=False).reset_index(drop=True)
active_full_df.index += 1
active_full_df.index.name = "Rank"

col1, col2 = st.columns(2)

with col1:
    active_display = active_full_df.copy().reset_index()
    active_display["Rank"] = active_display["Rank"].apply(add_medal)
    st.dataframe(active_display, use_container_width=True, hide_index=True)

with col2:
    fig3 = px.bar(
        active_full_df.reset_index(),
        x="Member",
        y="Expenses Involved In",
        color="Member",
        title="Number of Expenses per Member",
        text="Expenses Involved In"
    )
    fig3.update_traces(texttemplate="%{text}", textposition="outside")
    fig3.update_layout(
        showlegend=False,
        yaxis_range=[0, active_full_df["Expenses Involved In"].max() * 1.3]
    )
    st.plotly_chart(fig3, use_container_width=True)

st.divider()

# --- CATEGORY BREAKDOWN ---
st.subheader("🍕 Spending by Category")

category_df = unique_expenses.groupby("Category")["Amount ($)"].sum().reset_index()
category_df = category_df.sort_values("Amount ($)", ascending=False).reset_index(drop=True)
category_df.index += 1
category_df.index.name = "Rank"

col1, col2 = st.columns(2)

with col1:
    cat_display = category_df.copy().reset_index()
    cat_display["Rank"] = cat_display["Rank"].apply(add_medal)
    st.dataframe(cat_display, use_container_width=True, hide_index=True)

with col2:
    fig4 = px.pie(
        category_df.reset_index(),
        names="Category",
        values="Amount ($)",
        title="Spending Distribution by Category",
        hole=0.4
    )
    fig4.update_traces(textposition="inside", textinfo="percent+label")
    st.plotly_chart(fig4, use_container_width=True)

st.divider()

# --- FUN STATS ---
st.subheader("🎯 Fun Stats")

col1, col2, col3 = st.columns(3)

with col1:
    total_expenses = unique_expenses["ExpenseID"].nunique()
    total_spent = unique_expenses["Amount ($)"].sum()
    avg_per_expense = total_spent / total_expenses if total_expenses > 0 else 0
    st.metric("🧾 Avg Expense Size", f"${avg_per_expense:.2f}")

with col2:
    if not settlements_df.empty:
        total_settled = settlements_df["Amount ($)"].sum()
    else:
        total_settled = 0
    st.metric("✅ Total Settled", f"${total_settled:.2f}")

with col3:
    settlement_rate = (total_settled / total_spent * 100) if total_spent > 0 else 0
    st.metric("📊 Settlement Rate", f"{settlement_rate:.1f}%")