import streamlit as st
import pandas as pd
from datetime import datetime
from utils.file_helpers import load_groups, load_expenses, save_expenses

# --- PAGE CONFIG ---
st.set_page_config(page_title="Import Excel", page_icon="📥", layout="wide")

st.title("📥 Import from Excel")
st.write("Upload your expense Excel sheet and import transactions directly into your groups.")

st.divider()

# --- UPLOAD ---
st.subheader("📂 Upload Your Excel File")

uploaded_file = st.file_uploader("Upload Excel file (.xlsx)", type=["xlsx", "xls"])

if uploaded_file is None:
    st.info("Upload an Excel file above to get started.")
    st.stop()

# --- READ FILE ---
try:
    raw_df = pd.read_excel(uploaded_file, header=None)
except Exception as e:
    st.error(f"❌ Could not read file: {e}")
    st.stop()

# --- AUTO DETECT HEADER ROW ---
# find the row that looks most like a header
header_row = 0
for i, row in raw_df.iterrows():
    non_null = row.dropna().astype(str).str.lower().tolist()
    if any(word in " ".join(non_null) for word in ["date", "amount", "item", "split"]):
        header_row = i
        break

# re-read with correct header
df = pd.read_excel(uploaded_file, header=header_row)
df = df.dropna(how="all")  # drop completely empty rows

st.success(f"✅ File loaded! Found {len(df)} rows and {len(df.columns)} columns.")

st.divider()

# --- PREVIEW RAW DATA ---
st.subheader("👀 Raw Data Preview")
st.dataframe(df.head(20), use_container_width=True)

st.divider()

# --- COLUMN MAPPING ---
st.subheader("🗂️ Map Your Columns")
st.write("Tell us which column contains which information:")

columns = df.columns.tolist()
col_options = ["-- Skip --"] + columns

col1, col2, col3 = st.columns(3)

with col1:
    date_col = st.selectbox("📅 Date column", col_options,
                            index=col_options.index(columns[0]) if columns else 0)

    amount_col = st.selectbox("💰 Amount column", col_options,
                              index=col_options.index(columns[3]) if len(columns) > 3 else 0)

with col2:
    items_col = st.selectbox("🛒 Items / Description column", col_options,
                             index=col_options.index(columns[2]) if len(columns) > 2 else 0)

    split_col = st.selectbox("👥 Split Among column", col_options,
                             index=col_options.index(columns[4]) if len(columns) > 4 else 0)

with col3:
    card_col = st.selectbox("💳 Card / Source column (optional)", col_options,
                            index=col_options.index(columns[1]) if len(columns) > 1 else 0)

    splitwise_col = st.selectbox("✅ Splitwise YES/NO column (optional)", col_options,
                                 index=col_options.index(columns[5]) if len(columns) > 5 else 0)

st.divider()

# --- GROUP + MEMBER SETTINGS ---
st.subheader("👥 Group Settings")

groups_df = load_groups()

if groups_df.empty:
    st.warning("⚠️ No groups found. Please create a group first in the Groups page!")
    st.stop()

col1, col2 = st.columns(2)

with col1:
    group_names = groups_df["Group"].unique().tolist()
    selected_group = st.selectbox("Select group to import into", group_names)

with col2:
    members = groups_df[groups_df["Group"] == selected_group]["Member"].tolist()
    paid_by = st.selectbox("Who paid all these expenses?", members)

st.divider()

# --- CATEGORY MAPPING ---
st.subheader("🏷️ Default Category")
st.write("All imported expenses will use this category unless overridden.")

default_category = st.selectbox("Default Category", [
    "🛒 Groceries",
    "🍕 Food & Drink",
    "🚗 Transport",
    "🏠 Rent & Utilities",
    "🎬 Entertainment",
    "✈️ Travel",
    "💊 Health",
    "📦 Other"
])

st.divider()

# --- MEMBER CHECKBOXES ---
st.subheader("👥 Default Members to Include")
st.write("Select which members are included by default for equal splits:")

default_included = []
check_cols = st.columns(len(members))
for i, member in enumerate(members):
    with check_cols[i]:
        if st.checkbox(member, value=True, key=f"default_{member}"):
            default_included.append(member)

st.divider()

# --- PARSE SPLIT AMONG ---
def parse_split_among(split_text, members, default_included):
    """
    Parses the 'Split Among' text and returns a list of members to split with.
    Examples:
        'me nikhil'  → matches members containing those words
        'all 6'      → splits among all members
        'all'        → splits among all members
        NaN          → uses default_included
    """
    if pd.isna(split_text):
        return default_included

    split_text = str(split_text).lower().strip()

    # if it says "all" → include everyone
    if "all" in split_text:
        return members

    # otherwise try to match words to member names
    matched = []
    for member in members:
        if member.lower() in split_text:
            matched.append(member)

    # if nothing matched → use default
    return matched if matched else default_included


# --- PROCESS + PREVIEW ---
st.subheader("🔄 Processed Preview")
st.write("This is how your data will be imported:")

# build processed rows
if date_col == "-- Skip --" or amount_col == "-- Skip --":
    st.error("❌ Date and Amount columns are required!")
    st.stop()

processed_rows = []
skipped = 0

for _, row in df.iterrows():
    # skip if amount is missing or not a number
    try:
        amount = float(row[amount_col])
    except (ValueError, TypeError):
        skipped += 1
        continue

    # skip zero or negative amounts
    if amount <= 0:
        skipped += 1
        continue

    # skip if splitwise column says NO
    if splitwise_col != "-- Skip --":
        splitwise_val = str(row[splitwise_col]).strip().upper()
        if splitwise_val == "NO":
            skipped += 1
            continue

    # get date
    try:
        date = pd.to_datetime(row[date_col]).strftime("%Y-%m-%d %H:%M")
    except Exception:
        date = datetime.now().strftime("%Y-%m-%d %H:%M")

    # get items description
    items = str(row[items_col]).strip() if items_col != "-- Skip --" else "Imported Expense"
    if items == "nan":
        items = "Imported Expense"

    # get split among
    split_text = row[split_col] if split_col != "-- Skip --" else None
    split_members = parse_split_among(split_text, members, default_included)

    if not split_members:
        split_members = default_included

    # calculate equal share
    share = round(amount / len(split_members), 2)

    processed_rows.append({
        "Date": date,
        "Items": items,
        "Amount ($)": amount,
        "Split Among": ", ".join(split_members),
        "Share ($) each": share,
        "Num People": len(split_members)
    })

if not processed_rows:
    st.error("❌ No valid rows found after processing. Check your column mapping!")
    st.stop()

preview_df = pd.DataFrame(processed_rows)

st.dataframe(preview_df, use_container_width=True)

# summary metrics
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("✅ Valid Rows", len(processed_rows))
with col2:
    st.metric("⏭️ Skipped Rows", skipped)
with col3:
    st.metric("💰 Total Amount", f"${preview_df['Amount ($)'].sum():.2f}")
with col4:
    st.metric("📊 Avg Expense", f"${preview_df['Amount ($)'].mean():.2f}")

st.divider()

# --- IMPORT BUTTON ---
st.subheader("💾 Import into App")

if st.button("💾 Import All Transactions", type="primary"):

    import_rows = []

    for _, row in preview_df.iterrows():
        timestamp = row["Date"]
        expense_id = f"{timestamp}_{row['Items']}".replace(" ", "_")[:50]
        split_members = [m.strip() for m in row["Split Among"].split(",")]
        share = round(row["Amount ($)"] / len(split_members), 2)

        for member in split_members:
            import_rows.append({
                "ExpenseID": expense_id,
                "Date": timestamp,
                "Group": selected_group,
                "Expense": row["Items"],
                "Category": default_category,
                "Paid By": paid_by,
                "Amount ($)": row["Amount ($)"],
                "Split Type": "Equal split",
                "Member": member,
                "Share ($)": share
            })

    import_df = pd.DataFrame(import_rows)
    save_expenses(import_df)

    st.success(f"🎉 Successfully imported {len(processed_rows)} expenses into '{selected_group}'!")
    st.balloons()