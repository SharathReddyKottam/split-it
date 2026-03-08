import streamlit as st
import pandas as pd
from io import BytesIO
from utils.file_helpers import load_groups, load_expenses, load_settlements

# --- PAGE CONFIG ---
st.set_page_config(page_title="Export Excel", page_icon="📊", layout="centered")

st.title("📊 Export to Excel")
st.write("Download a fully formatted Excel report with multiple sheets.")

st.divider()

# --- LOAD DATA ---
groups_df = load_groups()
expenses_df = load_expenses()
settlements_df = load_settlements()

if groups_df.empty:
    st.warning("⚠️ No groups found. Please create a group first!")
    st.stop()

if expenses_df.empty:
    st.warning("⚠️ No expenses found. Add some expenses first!")
    st.stop()

# --- SETTINGS ---
st.subheader("⚙️ Report Settings")

col1, col2 = st.columns(2)

with col1:
    group_names = groups_df["Group"].unique().tolist()
    selected_group = st.selectbox("Select Group", group_names)

with col2:
    sheets_to_include = st.multiselect(
        "Sheets to include",
        ["Expenses", "Member Shares", "Balances", "Settlements", "Summary"],
        default=["Expenses", "Member Shares", "Balances", "Settlements", "Summary"]
    )

# date range
unique_expenses = expenses_df.drop_duplicates(subset="ExpenseID").copy()
unique_expenses["Date"] = pd.to_datetime(unique_expenses["Date"])
group_expenses = unique_expenses[unique_expenses["Group"] == selected_group]

if group_expenses.empty:
    st.info("No expenses found for this group.")
    st.stop()

min_date = group_expenses["Date"].min().date()
max_date = group_expenses["Date"].max().date()

date_range = st.date_input(
    "Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

if len(date_range) == 2:
    group_expenses = group_expenses[
        (group_expenses["Date"].dt.date >= date_range[0]) &
        (group_expenses["Date"].dt.date <= date_range[1])
        ]

st.divider()

# --- PREVIEW ---
st.subheader("👀 Preview")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("🧾 Expenses", len(group_expenses))
with col2:
    st.metric("💰 Total Spent", f"${group_expenses['Amount ($)'].sum():.2f}")
with col3:
    st.metric("📋 Sheets", len(sheets_to_include))

st.divider()

# --- EXCEL GENERATION ---
def generate_excel(group_name, expenses_df, settlements_df, groups_df, sheets):
    """Generates a formatted Excel file and returns it as bytes."""

    buffer = BytesIO()

    writer = pd.ExcelWriter(buffer, engine="xlsxwriter")
    workbook = writer.book

    # --- FIX: handle NaN and INF values ---
    workbook.nan_inf_to_errors = True

    # --- DEFINE FORMATS ---
    title_fmt = workbook.add_format({
        "bold": True,
        "font_size": 16,
        "font_color": "#1f77b4",
        "align": "left"
    })

    header_fmt = workbook.add_format({
        "bold": True,
        "font_size": 11,
        "font_color": "white",
        "bg_color": "#1f77b4",
        "align": "center",
        "border": 1
    })

    row_fmt_white = workbook.add_format({
        "font_size": 10,
        "bg_color": "#ffffff",
        "border": 1
    })

    row_fmt_blue = workbook.add_format({
        "font_size": 10,
        "bg_color": "#f0f4f8",
        "border": 1
    })

    money_fmt = workbook.add_format({
        "font_size": 10,
        "bg_color": "#ffffff",
        "border": 1,
        "num_format": "$#,##0.00"
    })

    money_fmt_blue = workbook.add_format({
        "font_size": 10,
        "bg_color": "#f0f4f8",
        "border": 1,
        "num_format": "$#,##0.00"
    })

    total_fmt = workbook.add_format({
        "bold": True,
        "font_size": 11,
        "bg_color": "#e8f0fe",
        "border": 1,
        "num_format": "$#,##0.00"
    })

    # --- HELPER: write a table to a sheet ---
    def write_table(worksheet, title, headers, rows, start_row=0):
        worksheet.write(start_row, 0, title, title_fmt)
        worksheet.set_row(start_row, 25)
        start_row += 2

        for col, header in enumerate(headers):
            worksheet.write(start_row, col, header, header_fmt)
        worksheet.set_row(start_row, 22)
        start_row += 1

        for i, row in enumerate(rows):
            fmt = row_fmt_blue if i % 2 == 0 else row_fmt_white
            money = money_fmt_blue if i % 2 == 0 else money_fmt
            for col, val in enumerate(row):
                # safely handle NaN
                if isinstance(val, float) and not pd.isna(val):
                    worksheet.write(start_row + i, col, val, money)
                elif isinstance(val, float) and pd.isna(val):
                    worksheet.write(start_row + i, col, "", fmt)
                else:
                    worksheet.write(start_row + i, col, val, fmt)
            worksheet.set_row(start_row + i, 20)

        return start_row + len(rows)

    # --- GET GROUP DATA ---
    members = groups_df[groups_df["Group"] == group_name]["Member"].tolist()

    # clean NaN before processing
    unique_exp = expenses_df.drop_duplicates(
        subset="ExpenseID"
    ).fillna("").copy()
    group_exp = unique_exp[unique_exp["Group"] == group_name]

    full_exp = expenses_df[
        expenses_df["Group"] == group_name
        ].fillna("").copy()

    group_set = settlements_df[
        settlements_df["Group"] == group_name
        ] if not settlements_df.empty else pd.DataFrame()

    # =====================
    # SHEET 1 — EXPENSES
    # =====================
    if "Expenses" in sheets:
        ws = workbook.add_worksheet("Expenses")
        ws.set_column("A:A", 12)
        ws.set_column("B:B", 25)
        ws.set_column("C:C", 20)
        ws.set_column("D:D", 15)
        ws.set_column("E:E", 12)

        headers = ["Date", "Expense", "Category", "Paid By", "Amount ($)"]
        rows = []
        for _, row in group_exp.iterrows():
            try:
                amount = float(row["Amount ($)"])
            except (ValueError, TypeError):
                amount = 0.0
            rows.append([
                str(row["Date"])[:10],
                str(row["Expense"]),
                str(row["Category"]),
                str(row["Paid By"]),
                amount
            ])

        last_row = write_table(
            ws, f"Expenses — {group_name}", headers, rows
        )

        try:
            total = float(group_exp["Amount ($)"].sum())
        except Exception:
            total = 0.0

        ws.write(last_row + 1, 3, "TOTAL", header_fmt)
        ws.write(last_row + 1, 4, total, total_fmt)

    # =====================
    # SHEET 2 — MEMBER SHARES
    # =====================
    if "Member Shares" in sheets:
        ws2 = workbook.add_worksheet("Member Shares")
        ws2.set_column("A:A", 12)
        ws2.set_column("B:B", 25)
        ws2.set_column("C:C", 15)
        ws2.set_column("D:D", 15)
        ws2.set_column("E:E", 12)

        headers2 = ["Date", "Expense", "Member", "Paid By", "Share ($)"]
        rows2 = []
        for _, row in full_exp.iterrows():
            try:
                share = float(row["Share ($)"])
            except (ValueError, TypeError):
                share = 0.0
            rows2.append([
                str(row["Date"])[:10],
                str(row["Expense"]),
                str(row["Member"]),
                str(row["Paid By"]),
                share
            ])

        write_table(
            ws2, f"Member Shares — {group_name}", headers2, rows2
        )

    # =====================
    # SHEET 3 — BALANCES
    # =====================
    if "Balances" in sheets:
        ws3 = workbook.add_worksheet("Balances")
        ws3.set_column("A:A", 20)
        ws3.set_column("B:B", 20)
        ws3.set_column("C:C", 15)

        owes_data = []
        for _, row in full_exp.iterrows():
            if str(row["Member"]) != str(row["Paid By"]):
                try:
                    share = float(row["Share ($)"])
                except (ValueError, TypeError):
                    share = 0.0
                owes_data.append({
                    "Who": row["Member"],
                    "Owes": row["Paid By"],
                    "Amount ($)": share
                })

        if owes_data:
            owes_df = pd.DataFrame(owes_data)
            summary = owes_df.groupby(
                ["Who", "Owes"]
            )["Amount ($)"].sum().reset_index()
            summary["Amount ($)"] = summary["Amount ($)"].round(2)

            headers3 = ["Who", "Owes To", "Amount ($)"]
            rows3 = []
            for _, row in summary.iterrows():
                rows3.append([
                    str(row["Who"]),
                    str(row["Owes"]),
                    float(row["Amount ($)"])
                ])

            write_table(
                ws3, f"Balances — {group_name}", headers3, rows3
            )
        else:
            ws3.write(0, 0, "No outstanding balances.", row_fmt_white)

    # =====================
    # SHEET 4 — SETTLEMENTS
    # =====================
    if "Settlements" in sheets:
        ws4 = workbook.add_worksheet("Settlements")
        ws4.set_column("A:A", 15)
        ws4.set_column("B:B", 20)
        ws4.set_column("C:C", 20)
        ws4.set_column("D:D", 15)

        headers4 = ["Date", "From", "To", "Amount ($)"]
        rows4 = []
        if not group_set.empty:
            for _, row in group_set.iterrows():
                try:
                    amount = float(row["Amount ($)"])
                except (ValueError, TypeError):
                    amount = 0.0
                rows4.append([
                    str(row["Date"])[:10],
                    str(row["From"]),
                    str(row["To"]),
                    amount
                ])

        write_table(
            ws4, f"Settlements — {group_name}", headers4, rows4
        )

    # =====================
    # SHEET 5 — SUMMARY
    # =====================
    if "Summary" in sheets:
        ws5 = workbook.add_worksheet("Summary")
        ws5.set_column("A:A", 30)
        ws5.set_column("B:B", 20)

        ws5.write(0, 0, f"Summary — {group_name}", title_fmt)
        ws5.set_row(0, 30)

        try:
            total_spent = float(group_exp["Amount ($)"].sum())
            avg_expense = float(group_exp["Amount ($)"].mean())
            biggest = float(group_exp["Amount ($)"].max())
        except Exception:
            total_spent = avg_expense = biggest = 0.0

        summary_data = [
            ["Group Name", group_name],
            ["Members", ", ".join(members)],
            ["Total Expenses", len(group_exp)],
            ["Total Spent ($)", total_spent],
            ["Average Expense ($)", avg_expense],
            ["Biggest Expense ($)", biggest],
            ["Total Settlements", len(group_set) if not group_set.empty else 0],
            ["Report Generated", pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")],
        ]

        for i, (label, value) in enumerate(summary_data):
            fmt = row_fmt_blue if i % 2 == 0 else row_fmt_white
            ws5.write(i + 2, 0, label, fmt)
            if isinstance(value, float):
                ws5.write(i + 2, 1, value, money_fmt)
            else:
                ws5.write(i + 2, 1, str(value), fmt)
            ws5.set_row(i + 2, 22)

    writer.close()
    buffer.seek(0)
    return buffer


# --- GENERATE & DOWNLOAD ---
st.subheader("⬇️ Generate & Download")

if st.button("📊 Generate Excel Report", type="primary"):
    with st.spinner("Generating Excel file..."):
        excel_buffer = generate_excel(
            selected_group,
            expenses_df,
            settlements_df,
            groups_df,
            sheets_to_include
        )

    st.download_button(
        label="⬇️ Download Excel File",
        data=excel_buffer,
        file_name=f"{selected_group}_expense_report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    st.success("✅ Excel file ready! Click Download above.")