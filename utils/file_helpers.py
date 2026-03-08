import pandas as pd
import os

# --- PATHS ---
GROUPS_FILE = "data/groups.csv"
EXPENSES_FILE = "data/expenses.csv"
SETTLEMENTS_FILE = "data/settlements.csv"

# --- HELPER: safe CSV reader ---
def safe_read_csv(filepath, columns):
    """Reads a CSV file safely — handles missing or empty files."""
    if not os.path.exists(filepath):
        return pd.DataFrame(columns=columns)
    try:
        df = pd.read_csv(filepath)
        if df.empty or len(df.columns) == 0:
            return pd.DataFrame(columns=columns)
        return df
    except pd.errors.EmptyDataError:
        return pd.DataFrame(columns=columns)

# --- GROUPS ---
def load_groups():
    return safe_read_csv(GROUPS_FILE, ["Group", "Member"])

def save_group(group_name, members):
    rows = [{"Group": group_name, "Member": m} for m in members]
    new_df = pd.DataFrame(rows)
    existing = load_groups()
    updated = pd.concat([existing, new_df], ignore_index=True)
    updated.to_csv(GROUPS_FILE, index=False)

def delete_group(group_name):
    df = load_groups()
    df = df[df["Group"] != group_name]
    df.to_csv(GROUPS_FILE, index=False)

# --- EXPENSES ---
def load_expenses():
    return safe_read_csv(EXPENSES_FILE, [
        "ExpenseID", "Date", "Group", "Expense", "Category",
        "Paid By", "Amount ($)", "Split Type", "Member", "Share ($)"
    ])

def save_expenses(new_df):
    existing = load_expenses()
    updated = pd.concat([existing, new_df], ignore_index=True)
    updated.to_csv(EXPENSES_FILE, index=False)

def delete_expense(expense_id):
    df = load_expenses()
    df = df[df["ExpenseID"] != expense_id]
    df.to_csv(EXPENSES_FILE, index=False)

# --- SETTLEMENTS ---
def load_settlements():
    return safe_read_csv(SETTLEMENTS_FILE, [
        "Date", "Group", "From", "To", "Amount ($)"
    ])

def save_settlement(group, from_person, to_person, amount):
    new_row = pd.DataFrame([{
        "Date": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "Group": group,
        "From": from_person,
        "To": to_person,
        "Amount ($)": amount
    }])
    existing = load_settlements()
    updated = pd.concat([existing, new_row], ignore_index=True)
    updated.to_csv(SETTLEMENTS_FILE, index=False)