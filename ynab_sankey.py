import requests
from datetime import datetime, timedelta
from collections import defaultdict

# User inputs
api_key = 'yourapikeyhere'
budget_id = 'yourbudgetidhere'

# Headers for API requests
headers = {
    'Authorization': f'Bearer {api_key}'
}

# Base URL for YNAB API requests
base_url = f'https://api.youneedabudget.com/v1/budgets/{budget_id}'

def get_month_range(year, month):
    """Returns the first and last day of the given month and year."""
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = datetime(year, month + 1, 1) - timedelta(days=1)
    return start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')

def fetch_categories():
    """Fetch all categories."""
    url = f'{base_url}/categories'
    response = requests.get(url, headers=headers).json()
    categories = {}
    for group in response['data']['category_groups']:
        for category in group['categories']:
            categories[category['id']] = {
                'name': category['name'],
                'group_name': group['name'],
                'budgeted': 0  # Initialize budgeted as 0; will update later
            }
    return categories

def update_categories_with_monthly_budget(categories, year, month):
    """Update categories with the budgeted amounts for the specified month."""
    month_for_api = f"{year}-{month:02d}-01"  # YYYY-MM-DD format required for the API endpoint
    url = f'{base_url}/months/{month_for_api}'
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(url)
        print(f"Error fetching monthly budget details: {response.status_code}")
        return categories, {}  # If failed, return categories without changes and an empty dict
    
    monthly_data = response.json()['data']['month']['categories']
    savings_investing_budgeted = {}
    for category in monthly_data:
        if category['id'] in categories:
            categories[category['id']]['budgeted'] = round(category['budgeted'] / 1000)
            if categories[category['id']]['group_name'].lower().find('saving & investing') != -1:
                savings_investing_budgeted[categories[category['id']]['name']] = categories[category['id']]['budgeted']
    
    return categories, savings_investing_budgeted


def fetch_transactions(categories, year, month):
    """Fetch transactions for the specified month and manually filter by date."""
    start_date, end_date = get_month_range(year, month)
    print(f"Debugging - Fetching transactions from {start_date} to {end_date}")
    
    url = f'{base_url}/transactions?since_date={start_date}'
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Error fetching transactions: {response.status_code}")
        return defaultdict(float), defaultdict(lambda: defaultdict(float))

    transactions_data = response.json()
    transactions = transactions_data['data']['transactions']

    # Manually filter transactions to include only those within the specified date range
    filtered_transactions = [
        transaction for transaction in transactions if start_date <= transaction['date'] <= end_date
    ]
    
    income_by_payee = defaultdict(float)
    expenditures_by_category_group = defaultdict(lambda: defaultdict(float))

    for transaction in filtered_transactions:
        category_id = transaction.get('category_id')
        if category_id in categories:
            category_info = categories[category_id]
            amount = round(transaction['amount'] / 1000)  # Convert from milliunits to units
            if amount > 0:
                income_by_payee[transaction['payee_name']] += amount
            else:
                expenditures_by_category_group[category_info['group_name']][category_info['name']] += abs(amount)

    return income_by_payee, expenditures_by_category_group

def format_and_output_data(income_by_payee, expenditures_by_category_group, savings_investing_budgeted, year, month):
    filename = f'ynab_sankey_{year}_{month:02d}.txt'
    with open(filename, 'w') as file:
        # Output income streams
        for payee, amount in income_by_payee.items():
            file.write(f"{payee} [{amount}] Budget\n")
        
        file.write("\n")  # Separate sections

        # Output expenditures by category group, linking them back to Budget
        for group_name, categories in expenditures_by_category_group.items():
            group_total = sum(categories.values())
            if group_total > 0:
                file.write(f"Budget [{group_total}] {group_name}\n")
            for category_name, amount in categories.items():
                if amount > 0:
                    file.write(f"{group_name} [{amount}] {category_name}\n")

        # Handle "Saving & Investing" with budgeted amounts
        total_budgeted = sum(savings_investing_budgeted.values())
        if total_budgeted > 0:
            file.write(f"\nBudget [{total_budgeted}] Saving & Investing\n")
            for category_name, budgeted_amount in savings_investing_budgeted.items():
                if budgeted_amount > 0:  # Ignore 0 amounts
                    file.write(f"Saving & Investing [{budgeted_amount}] {category_name}\n")

def main():
    print("Please select the month and year you want information for.")
    year = int(input("Enter the year (YYYY): "))
    month = int(input("Enter the month (MM): "))

    categories = fetch_categories()  # Fetch all categories first
    categories, savings_investing_budgeted = update_categories_with_monthly_budget(categories, year, month)  # Update with monthly data
    income_by_payee, expenditures_by_category_group = fetch_transactions(categories, year, month)
    format_and_output_data(income_by_payee, expenditures_by_category_group, savings_investing_budgeted, year, month)


if __name__ == "__main__":
    main()
