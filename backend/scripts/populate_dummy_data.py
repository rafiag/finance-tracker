"""
Script to populate Google Sheets with dummy transaction data for testing.

This script generates realistic dummy data with:
- Income, Expense, and Transfer transactions
- Multiple categories and subcategories fetched from the sheet
- Multiple months of data (last 3 months)
- Various accounts fetched from the sheet
- Some flagged transactions for testing
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

# Realistic amount ranges (fallback if not in master data mapping)
DEFAULT_RANGES = {
    'Expense': (10000, 500000),
    'Income': (1000000, 10000000),
    'Transfer': (50000, 1000000)
}

# Mapping specific categories to realistic ranges for better dummy data
CATEGORY_LIMITS = {
    'Food': (25000, 500000),
    'Transport': (50000, 300000),
    'Utilities': (500000, 3000000),
    'Shopping': (100000, 2000000),
    'Salary': (5000000, 20000000),
    'Rent': (2000000, 7000000),
    'Investment': (500000, 5000000)
}

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
    """Fetch accounts and categories from the Settings sheets."""
    print("📋 Fetching master data from sheets...")
    
    # Fetch Accounts
    accounts_sheet = spreadsheet.worksheet('Settings_Accounts')
    accounts_data = accounts_sheet.get_all_records()
    accounts = [row['Account Name'] for row in accounts_data]
    
    # Fetch Categories
    categories_sheet = spreadsheet.worksheet('Settings_Categories')
    categories_data = categories_sheet.get_all_records()
    
    # Group categories by type
    master_categories = {
        'Expense': [],
        'Income': [],
        'Transfer': []
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
        min_amt, max_amt = DEFAULT_RANGES[trans_type]
        if category in CATEGORY_LIMITS:
            min_amt, max_amt = CATEGORY_LIMITS[category]
        elif subcategory in CATEGORY_LIMITS:
            min_amt, max_amt = CATEGORY_LIMITS[subcategory]
            
        # Notes
        notes = EXPENSE_NOTES if trans_type == 'Expense' else (INCOME_NOTES if trans_type == 'Income' else TRANSFER_NOTES)
        
        transaction = {
            'Date': generate_random_date(),
            'Account': random.choice(accounts),
            'Category': category,
            'Subcategory': subcategory,
            'Note': random.choice(notes),
            'Amount': random.randint(min_amt, max_amt),
            'Type': trans_type,
            'Status': 'Flagged' if trans_type == 'Expense' and random.random() < 0.1 else 'Normal'
        }
        transactions.append(transaction)
    
    return transactions


def connect_to_sheet():
    """Connect to Google Sheets."""
    print("🔗 Connecting to Google Sheets...")
    creds = Credentials.from_service_account_file(CREDENTIALS_PATH, scopes=SCOPES)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(SHEET_ID)
    print(f"✅ Connected to: {spreadsheet.title}")
    return spreadsheet


def populate_transactions(spreadsheet):
    """Populate the Transactions sheet with dummy data."""
    # 1. Fetch Master Data
    accounts, master_categories = fetch_master_data(spreadsheet)
    
    if not accounts:
        print("❌ Error: No accounts found in Settings_Accounts. Please populate it first.")
        return

    print("\n📝 Generating dummy transactions...")
    
    # 2. Generate all transactions
    all_transactions = []
    all_transactions.extend(generate_transactions(140, 'Expense', accounts, master_categories['Expense']))
    all_transactions.extend(generate_transactions(40, 'Income', accounts, master_categories['Income']))
    all_transactions.extend(generate_transactions(25, 'Transfer', accounts, master_categories['Transfer']))
    
    # Sort by date
    all_transactions.sort(key=lambda x: x['Date'])
    
    # 3. Write to sheet
    print(f"📤 Writing {len(all_transactions)} transactions to Transactions sheet...")
    worksheet = spreadsheet.worksheet('Transactions')
    
    # Clear existing data
    worksheet.clear()
    
    # Write header
    header = ['Date', 'Account', 'Category', 'Subcategory', 'Note', 'Amount', 'Type', 'Status']
    worksheet.update([header], 'A1:H1')
    
    # Format header
    worksheet.format('A1:H1', {
        'textFormat': {'bold': True},
        'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9}
    })
    
    # Prepare rows
    rows = []
    for t in all_transactions:
        rows.append([
            t['Date'], t['Account'], t['Category'], t['Subcategory'],
            t['Note'], t['Amount'], t['Type'], t['Status']
        ])
    
    # Write data
    if rows:
        worksheet.update(rows, f'A2:H{len(rows) + 1}')
    
    print(f"✅ Successfully wrote {len(rows)} transactions to sheet!")
    return all_transactions


def show_summary(all_transactions):
    """Show a summary of the generated data."""
    if not all_transactions:
        return

    print("\n" + "="*60)
    print("📊 DATA SUMMARY")
    print("="*60)
    
    dates = [datetime.strptime(t['Date'], '%Y-%m-%d') for t in all_transactions]
    print(f"\n📅 Date Range: {min(dates).strftime('%Y-%m-%d')} to {max(dates).strftime('%Y-%m-%d')}")
    
    months = sorted(set(d.strftime('%Y-%m') for d in dates))
    print(f"📆 Months Covered: {len(months)} ({', '.join(months)})")
    
    types = {'Income': 0, 'Expense': 0, 'Transfer': 0}
    totals = {'Income': 0, 'Expense': 0, 'Transfer': 0}
    for t in all_transactions:
        types[t['Type']] += 1
        totals[t['Type']] += t['Amount']
        
    print(f"\n💰 Totals:")
    for k, v in types.items():
        print(f"   - {k}: {v} transactions (IDR {totals[k]:,.0f})")
    
    print(f"   - Net Savings: IDR {(totals['Income'] - totals['Expense']):,.0f}")
    print("\n" + "="*60)


def main():
    print("="*60)
    print("🚀 UPDATED DUMMY DATA POPULATION SCRIPT")
    print("="*60)
    
    try:
        spreadsheet = connect_to_sheet()
        all_transactions = populate_transactions(spreadsheet)
        show_summary(all_transactions)
        print("\n✅ All done! Data is synchronized with your Settings tabs.")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

