import pandas as pd

def calculate_balances(expenses_df, settlements_df, group_name):
    """
    Returns a dataframe showing the net balance of each person in a group.
    Positive = they are owed money
    Negative = they owe money
    """

    balances = {}

    # filter to this group only
    group_expenses = expenses_df[expenses_df["Group"] == group_name]
    group_settlements = settlements_df[settlements_df["Group"] == group_name]

    # go through each expense row
    for _, row in group_expenses.iterrows():
        paid_by = row["Paid By"]
        member = row["Member"]
        share = row["Share ($)"]

        # person who paid is owed money — add to their balance
        if paid_by not in balances:
            balances[paid_by] = 0
        balances[paid_by] += share

        # person who owes reduces the payer's balance
        if member not in balances:
            balances[member] = 0
        if member != paid_by:
            balances[member] -= share

    # subtract any settlements
    for _, row in group_settlements.iterrows():
        from_person = row["From"]
        to_person = row["To"]
        amount = row["Amount ($)"]

        if from_person not in balances:
            balances[from_person] = 0
        if to_person not in balances:
            balances[to_person] = 0

        balances[from_person] += amount
        balances[to_person] -= amount

    # turn into a clean dataframe
    result = pd.DataFrame([
        {"Member": person, "Balance ($)": round(bal, 2)}
        for person, bal in balances.items()
    ])

    return result