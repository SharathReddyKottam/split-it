import streamlit as st
import pandas as pd
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.platypus import HRFlowable
from utils.file_helpers import load_groups, load_expenses, load_settlements

# --- PAGE CONFIG ---
st.set_page_config(page_title="Export PDF", page_icon="📄", layout="centered")

st.title("📄 Export to PDF")
st.write("Download a full expense report for any group.")

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

# --- FILTERS ---
st.subheader("⚙️ Report Settings")

col1, col2 = st.columns(2)

with col1:
    group_names = groups_df["Group"].unique().tolist()
    selected_group = st.selectbox("Select Group", group_names)

with col2:
    report_type = st.selectbox("Report Type", [
        "Full Report",
        "Expenses Only",
        "Balances Only",
        "Settlements Only"
    ])

# date range filter
unique_expenses = expenses_df.drop_duplicates(subset="ExpenseID").copy()
unique_expenses["Date"] = pd.to_datetime(unique_expenses["Date"])

group_expenses = unique_expenses[unique_expenses["Group"] == selected_group]

if not group_expenses.empty:
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

# --- REPORT PREVIEW ---
st.subheader("👀 Report Preview")

if group_expenses.empty:
    st.info("No expenses found for this group in the selected date range.")
    st.stop()

# expenses table
display_cols = ["Date", "Expense", "Category", "Paid By", "Amount ($)"]
st.write("**Expenses:**")
st.dataframe(group_expenses[display_cols], use_container_width=True)

total_spent = group_expenses["Amount ($)"].sum()
st.metric("💰 Total Spent", f"${total_spent:.2f}")

st.divider()

# --- PDF GENERATION FUNCTION ---
def generate_pdf(group_name, expenses_df, settlements_df, groups_df, report_type):
    """Generates a PDF report and returns it as bytes."""

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch
    )

    # styles
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "Title",
        parent=styles["Title"],
        fontSize=24,
        textColor=colors.HexColor("#1f77b4"),
        spaceAfter=6
    )

    heading_style = ParagraphStyle(
        "Heading",
        parent=styles["Heading2"],
        fontSize=14,
        textColor=colors.HexColor("#1f77b4"),
        spaceBefore=12,
        spaceAfter=6
    )

    normal_style = styles["Normal"]

    # content list — everything we add goes in here
    content = []

    # --- HEADER ---
    content.append(Paragraph("💸 Split It", title_style))
    content.append(Paragraph(f"Expense Report — {group_name}", heading_style))
    content.append(Paragraph(
        f"Generated on: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}",
        normal_style
    ))
    content.append(Spacer(1, 0.2 * inch))
    content.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
    content.append(Spacer(1, 0.2 * inch))

    # --- MEMBERS SECTION ---
    members = groups_df[groups_df["Group"] == group_name]["Member"].tolist()
    content.append(Paragraph("👥 Group Members", heading_style))
    content.append(Paragraph(", ".join(members), normal_style))
    content.append(Spacer(1, 0.2 * inch))

    # --- EXPENSES SECTION ---
    if report_type in ["Full Report", "Expenses Only"]:
        content.append(Paragraph("🧾 Expenses", heading_style))

        if expenses_df.empty:
            content.append(Paragraph("No expenses found.", normal_style))
        else:
            # table header
            expense_data = [["Date", "Expense", "Category", "Paid By", "Amount ($)"]]

            for _, row in expenses_df.iterrows():
                expense_data.append([
                    str(row["Date"])[:10],
                    str(row["Expense"]),
                    str(row["Category"]),
                    str(row["Paid By"]),
                    f"${row['Amount ($)']:.2f}"
                ])

            # total row
            expense_data.append([
                "", "", "", "TOTAL",
                f"${expenses_df['Amount ($)'].sum():.2f}"
            ])

            # build table
            expense_table = Table(
                expense_data,
                colWidths=[1.0*inch, 1.8*inch, 1.5*inch, 1.2*inch, 1.0*inch]
            )

            expense_table.setStyle(TableStyle([
                # header row
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f77b4")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 10),
                ("ALIGN", (0, 0), (-1, 0), "CENTER"),

                # data rows
                ("FONTSIZE", (0, 1), (-1, -1), 9),
                ("ROWBACKGROUNDS", (0, 1), (-1, -2),
                 [colors.white, colors.HexColor("#f0f4f8")]),
                ("ALIGN", (-1, 0), (-1, -1), "RIGHT"),

                # total row
                ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#e8f0fe")),
                ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),

                # grid
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ROWHEIGHT", (0, 0), (-1, -1), 20),
            ]))

            content.append(expense_table)
            content.append(Spacer(1, 0.2 * inch))

    # --- BALANCES SECTION ---
    if report_type in ["Full Report", "Balances Only"]:
        content.append(Paragraph("⚖️ Balances", heading_style))

        # calculate who owes who
        full_expenses = expenses_df.copy() if not expenses_df.empty else pd.DataFrame()
        owes_data = []

        for _, row in expenses_df.iterrows():
            paid_by = row["Paid By"]
            member = row["Member"] if "Member" in row else None
            share = row["Share ($)"] if "Share ($)" in row else 0

            if member and member != paid_by:
                owes_data.append({
                    "Who": member,
                    "Owes": paid_by,
                    "Amount ($)": share
                })

        if owes_data:
            owes_df = pd.DataFrame(owes_data)
            summary = owes_df.groupby(
                ["Who", "Owes"]
            )["Amount ($)"].sum().reset_index()
            summary["Amount ($)"] = summary["Amount ($)"].round(2)

            balance_data = [["Person", "Owes To", "Amount ($)"]]
            for _, row in summary.iterrows():
                balance_data.append([
                    row["Who"],
                    row["Owes"],
                    f"${row['Amount ($)']:.2f}"
                ])

            balance_table = Table(
                balance_data,
                colWidths=[2.0*inch, 2.0*inch, 1.5*inch]
            )
            balance_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f77b4")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1),
                 [colors.white, colors.HexColor("#f0f4f8")]),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ALIGN", (-1, 0), (-1, -1), "RIGHT"),
                ("ROWHEIGHT", (0, 0), (-1, -1), 20),
            ]))

            content.append(balance_table)
        else:
            content.append(Paragraph("No outstanding balances.", normal_style))

        content.append(Spacer(1, 0.2 * inch))

    # --- SETTLEMENTS SECTION ---
    if report_type in ["Full Report", "Settlements Only"]:
        content.append(Paragraph("✅ Settlements", heading_style))

        group_settlements = settlements_df[
            settlements_df["Group"] == group_name
            ] if not settlements_df.empty else pd.DataFrame()

        if group_settlements.empty:
            content.append(Paragraph("No settlements recorded.", normal_style))
        else:
            settlement_data = [["Date", "From", "To", "Amount ($)"]]
            for _, row in group_settlements.iterrows():
                settlement_data.append([
                    str(row["Date"])[:10],
                    row["From"],
                    row["To"],
                    f"${row['Amount ($)']:.2f}"
                ])

            settlement_table = Table(
                settlement_data,
                colWidths=[1.5*inch, 1.8*inch, 1.8*inch, 1.4*inch]
            )
            settlement_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f77b4")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1),
                 [colors.white, colors.HexColor("#f0f4f8")]),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ALIGN", (-1, 0), (-1, -1), "RIGHT"),
                ("ROWHEIGHT", (0, 0), (-1, -1), 20),
            ]))
            content.append(settlement_table)

        content.append(Spacer(1, 0.2 * inch))

    # --- FOOTER ---
    content.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
    content.append(Spacer(1, 0.1 * inch))
    content.append(Paragraph(
        "Generated by Split It — split-it.streamlit.app",
        ParagraphStyle("Footer", parent=styles["Normal"],
                       fontSize=8, textColor=colors.grey)
    ))

    # build PDF
    doc.build(content)
    buffer.seek(0)
    return buffer


# --- GENERATE & DOWNLOAD BUTTON ---
st.subheader("⬇️ Generate & Download")

if st.button("📄 Generate PDF Report", type="primary"):
    with st.spinner("Generating PDF..."):

        # get full expense data including member shares
        full_group_expenses = expenses_df[
            expenses_df["Group"] == selected_group
            ].copy()
        full_group_expenses["Date"] = pd.to_datetime(
            full_group_expenses["Date"]
        )

        if len(date_range) == 2:
            full_group_expenses = full_group_expenses[
                (full_group_expenses["Date"].dt.date >= date_range[0]) &
                (full_group_expenses["Date"].dt.date <= date_range[1])
                ]

        # get unique expenses only for expense table
        unique_for_pdf = full_group_expenses.drop_duplicates(
            subset="ExpenseID"
        )

        pdf_buffer = generate_pdf(
            selected_group,
            unique_for_pdf,
            settlements_df,
            groups_df,
            report_type
        )

    st.download_button(
        label="⬇️ Download PDF",
        data=pdf_buffer,
        file_name=f"{selected_group}_expense_report.pdf",
        mime="application/pdf"
    )

    st.success("✅ PDF ready! Click Download PDF above.")