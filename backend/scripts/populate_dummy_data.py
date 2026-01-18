"""
Script to populate Google Sheets with dummy data for testing.

This script generates realistic dummy data with:
- Income, Expense, Transfer, and Investment transactions
- Multiple categories and subcategories fetched from the sheet
- Multiple months of data (last 3 months)
- Various accounts fetched from the sheet
- Investments data for portfolio tracking
"""

import os
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv
import gspread
from google.oauth2.service_account import Credentials

# Load environment variables
load_dotenv()

# Google Sheets configuration
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
SHEET_ID = os.getenv('GOOGLE_SHEET_ID')
CREDENTIALS_PATH = os.getenv('GOOGLE_SHEETS_CREDENTIALS_PATH', './credentials.json')

# Realistic amount ranges
DEFAULT_RANGES = {
    'Expense': (10000, 500000),
    'Income': (1000000, 10000000),
    'Transfer': (50000, 1000000)
}

# Mapping specific categories to realistic ranges
CATEGORY_LIMITS = {
    'Food': (25000, 500000),
    'Transport': (50000, 300000),
    'Utilities': (500000, 3000000),
    'Shopping': (100000, 2000000),
    'Salary': (5000000, 20000000),
    'Rent': (2000000, 7000000),
    'Investment': (500000, 5000000)
}

# Stock data for dummy investments
STOCK_SYMBOLS = ['AAPL', 'GOOGL', 'AMZN', 'MSFT', 'TSLA', 'META', 'NFLX', 'NVDA']

# Notes templates
EXPENSE_NOTES = [
    'Weekly shopping', 'Monthly subscription', 'Dinner with friends', 
    'Fuel refill', 'Emergency purchase', 'Planned expense', 
    'Gift for family', 'Home supplies', 'Personal care', 'Entertainment'
]

INCOME_NOTES = [
    'Monthly salary', 'Bonus payment', 'Side project payment', 
    'Freelance work', 'Investment return', 'Commission', 
    'Reimbursement', 'Gift received'
]

TRANSFER_NOTES = [
    'Transfer to savings', 'Top up e-wallet', 'Move funds between accounts', 
    'Emergency fund allocation', 'Investment transfer'
]


def generate_random_date(start_months_ago=3):
    """Generate a random date within the last N months."""
    today = datetime.now()
    start_date = today - timedelta(days=30 * start_months_ago)
    random_days = random.randint(0, (today - start_date).days)
    random_date = start_date + timedelta(days=random_days)
    return random_date.strftime('%Y-%m-%d')


def fetch_master_data(spreadsheet):
    """Fetch accounts and categories from the sheets."""
    print("📋 Fetching master data from sheets...")
    
    # Fetch Accounts (use Settings_Accounts tab name as per gsheets_handler.py)
    accounts_sheet = spreadsheet.worksheet('Settings_Accounts')
    accounts_data = accounts_sheet.get_all_records()
    accounts = [row['Account Name'] for row in accounts_data]

    # Fetch Categories (use Settings_Categories tab name as per gsheets_handler.py)
    categories_sheet = spreadsheet.worksheet('Settings_Categories')
    categories_data = categories_sheet.get_all_records()
    
    # Group categories by type
    master_categories = {
        'Expense': [],
        'Income': [],
        'Transfer': [],
        'Investment': [],
        'Asset': []  # For asset purchases
    }
    
    for row in categories_data:
        t = row['Type']
        if t in master_categories:
            master_categories[t].append({
                'category': row['Category'],
                'subcategory': row['Subcategory']
            })
    
    print(f"✅ Found {len(accounts)} accounts and {sum(len(v) for v in master_categories.values())} category combinations.")
    return accounts, master_categories


def generate_transactions(count, trans_type, accounts, categories_list):
    """Generate dummy transactions for a specific type."""
    transactions = []
    
    if not categories_list:
        print(f"⚠️ No categories found for type: {trans_type}. Skipping...")
        return []

    for _ in range(count):
        cat_info = random.choice(categories_list)
        category = cat_info['category']
        subcategory = cat_info['subcategory']
        
        # Determine amount range
        if trans_type == 'Asset':
            min_amt, max_amt = (500000, 5000000)  # Investment purchase amounts
        else:
            min_amt, max_amt = DEFAULT_RANGES.get(trans_type, (10000, 1000000))
            if category in CATEGORY_LIMITS:
                min_amt, max_amt = CATEGORY_LIMITS[category]
            elif subcategory in CATEGORY_LIMITS:
                min_amt, max_amt = CATEGORY_LIMITS[subcategory]
            
        # Description
        if trans_type == 'Asset':
            descriptions = ['Stock purchase', 'Investment buy', 'Asset acquisition', 'Portfolio investment']
        else:
            descriptions = EXPENSE_NOTES if trans_type == 'Expense' else (INCOME_NOTES if trans_type == 'Income' else TRANSFER_NOTES)
        
        transaction = {
            'Date': generate_random_date(),
            'Account': random.choice(accounts),
            'Category': category,
            'Subcategory': subcategory,
            'Description': random.choice(descriptions),
            'Amount': random.randint(min_amt, max_amt),
            'Type': trans_type,
            'Status': 'flagged' if trans_type == 'Expense' and random.random() < 0.1 else 'normal'
        }
        transactions.append(transaction)
    
    return transactions


def generate_investments(count, accounts):
    """Generate dummy investment data."""
    investments = []
    # Filter for investment-type accounts if possible
    investment_accounts = [acc for acc in accounts if 'Investment' in acc or 'RDN' in acc]
    if not investment_accounts:
        investment_accounts = accounts
    
    for _ in range(count):
        symbol = random.choice(STOCK_SYMBOLS)
        shares = random.randint(1, 100)
        avg_buy_price = random.uniform(50, 500)
        current_price = avg_buy_price * random.uniform(0.8, 1.5)
        total_value = shares * current_price
        realized_pl = random.uniform(-1000, 5000) if random.random() < 0.3 else 0
        
        investment = {
            'Purchase Date': generate_random_date(start_months_ago=6),
            'Account': random.choice(investment_accounts),
            'Symbol': symbol,
            'Shares': shares,
            'Avg Buy Price': round(avg_buy_price, 2),
            'Current Price': round(current_price, 2),
            'Total Value': round(total_value, 2),
            'Realized P/L': round(realized_pl, 2)
        }
        investments.append(investment)
    
    # Sort by date
    investments.sort(key=lambda x: x['Purchase Date'])
    return investments


def connect_to_sheet():
    """Connect to Google Sheets."""
    print("🔗 Connecting to Google Sheets...")
    creds = Credentials.from_service_account_file(CREDENTIALS_PATH, scopes=SCOPES)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(SHEET_ID)
    print(f"✅ Connected to: {spreadsheet.title}")
    return spreadsheet


def populate_transactions(spreadsheet, accounts, master_categories):
    """Populate the Transactions sheet."""
    print("\n📝 Generating dummy transactions...")
    
    all_transactions = []
    all_transactions.extend(generate_transactions(140, 'Expense', accounts, master_categories['Expense']))
    all_transactions.extend(generate_transactions(40, 'Income', accounts, master_categories['Income']))
    all_transactions.extend(generate_transactions(25, 'Transfer', accounts, master_categories['Transfer']))
    # Generate Asset transactions (investment purchases) if Investment categories exist
    if master_categories.get('Investment'):
        all_transactions.extend(generate_transactions(15, 'Asset', accounts, master_categories['Investment']))
    
    # Sort by date
    all_transactions.sort(key=lambda x: x['Date'])
    
    print(f"📤 Writing {len(all_transactions)} transactions to Transactions sheet...")
    worksheet = spreadsheet.worksheet('Transactions')
    worksheet.clear()
    
    header = ['Date', 'Account', 'Category', 'Subcategory', 'Description', 'Amount', 'Type', 'Status']
    rows = [header]
    for t in all_transactions:
        rows.append([
            t['Date'], t['Account'], t['Category'], t['Subcategory'],
            t['Description'], t['Amount'], t['Type'], t['Status']
        ])
    
    worksheet.update(rows, f'A1:H{len(rows)}')
    
    # Format header
    worksheet.format('A1:H1', {
        'textFormat': {'bold': True},
        'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9}
    })
    print(f"✅ Successfully wrote {len(rows)-1} transactions!")
    return all_transactions


def populate_investments(spreadsheet, accounts):
    """Populate the Investments sheet."""
    print("\n📈 Generating dummy investments...")
    investments = generate_investments(15, accounts)
    
    print(f"📤 Writing {len(investments)} holdings to Investments sheet...")
    worksheet = spreadsheet.worksheet('Investments')
    worksheet.clear()
    
    header = ['Purchase Date', 'Account', 'Symbol', 'Shares', 'Avg Buy Price', 'Current Price', 'Total Value', 'Realized P/L']
    rows = [header]
    for i in investments:
        rows.append([
            i['Purchase Date'], i['Account'], i['Symbol'], i['Shares'], i['Avg Buy Price'],
            i['Current Price'], i['Total Value'], i['Realized P/L']
        ])
    
    worksheet.update(rows, f'A1:H{len(rows)}')
    
    # Format header
    worksheet.format('A1:H1', {
        'textFormat': {'bold': True},
        'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9}
    })
    print(f"✅ Successfully wrote {len(investments)} investments!")


def main():
    print("="*60)
    print("🚀 UPDATED DUMMY DATA POPULATION SCRIPT")
    print("="*60)
    
    try:
        spreadsheet = connect_to_sheet()
        accounts, master_categories = fetch_master_data(spreadsheet)
        
        if not accounts:
            print("❌ Error: No accounts found. Please populate Accounts sheet first.")
            return

        populate_transactions(spreadsheet, accounts, master_categories)
        populate_investments(spreadsheet, accounts)
        
        print("\n✅ All done! Data is synchronized with your Settings tabs.")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

