import random


def generate_table():
    """Generate a realistic interactive table with deferred payments and precise loan payment calculations."""
    num_years = random.randint(4, 8)  # Number of years (total period of the loan)
    deferment_years = random.randint(1, num_years - 2)  # Deferment period (0 means immediate payments)
    interest_rate = random.randint(5, 15) / 100  # Annual interest rate (5% to 15%)
    initial_balance = random.randint(1, 20) * 1000  # Initial loan balance ($1,000 to $20,000)

    # Calculate the annuity factor (A|P, i%, n)
    def annuity_factor(i, n):
        if i == 0:  # If 0% interest, avoid division by zero
            return n
        return (i * (1 + i) ** n) / ((1 + i) ** n - 1)

    # Determine loan payment size (A)
    repayment_years = num_years - deferment_years
    capitalized_balance = initial_balance * (1 + interest_rate) ** deferment_years
    if repayment_years > 0:
        loan_payment = capitalized_balance * annuity_factor(interest_rate, repayment_years)
    else:
        loan_payment = 0  # If no repayment period is left, set payment to 0

    table = []
    missing_cell = None
    ub_previous = initial_balance
    uia_previous = 0

    for year in range(1, num_years + 1):
        row = {}
        row["Year"] = year
        row["UB"] = round(ub_previous, 2) if ub_previous else 0  # Unpaid Balance

        row["Int"] = round(interest_rate * ub_previous, 2) if ub_previous else 0  # Interest During Year
        row["UIB"] = round(row["Int"] + uia_previous, 2)  # Unpaid Interest Before Payment
        row["AO"] = round(row["UB"] + row["Int"], 2)  # Amount Owed

        # Loan payment logic: no payment during deferment years
        row["Ad"] = 0 if year <= deferment_years else round(loan_payment, 2)

        # Interest payment logic
        row["IPmt"] = round(min(row["UIB"], row["Ad"]), 2)
        row["PPmt"] = round(row["Ad"] - row["IPmt"], 2)  # Principal payment
        row["UIA"] = round(row["UIB"] - row["IPmt"], 2)  # Unpaid Interest After Payment
        row["UBA"] = round(row["AO"] - row["Ad"], 2)  # Unpaid Balance After Payment

        # Update tracking variables for subsequent rows
        ub_previous = row["UBA"]
        uia_previous = row["UIA"]

        table.append(row)

    # Randomly blank out one cell in the table
    columns = ["UB", "Int", "UIB", "AO", "Ad", "IPmt", "PPmt", "UIA", "UBA"]
    # Exclude critical columns (UB, Int, Ad) from being blanked
    columns = ["UIB", "AO", "IPmt", "PPmt", "UIA", "UBA"]
    random_row = random.choice(table) if table else {}
    blank_column = random.choice(columns) if random_row else None

    if random_row and blank_column:
        missing_cell = {
            "Year": random_row["Year"],
            "Column": blank_column,
            "CorrectValue": random_row.get(blank_column, 0),
        }
        random_row[blank_column] = None

    print("DF", deferment_years)

    return table, missing_cell, deferment_years