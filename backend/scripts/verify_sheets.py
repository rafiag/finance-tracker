import os
import gspread
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials

# Load environment variables
load_dotenv()

def verify_gsheet():
    results = []
    def log(msg):
        print(msg)
        results.append(msg)

    log("--- Google Sheets Verification ---")
    
    sheet_id = os.getenv("GOOGLE_SHEET_ID")
    creds_path = os.getenv("GOOGLE_SHEETS_CREDENTIALS_PATH", "credentials.json")
    
    if not sheet_id:
        log("Error: GOOGLE_SHEET_ID not found in .env")
        return
    if not os.path.exists(creds_path):
        log(f"Error: Credentials file not found at {creds_path}")
        return

    # Authenticate
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    try:
        creds = Credentials.from_service_account_file(creds_path, scopes=scopes)
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_key(sheet_id)
        log(f"Successfully connected to spreadsheet: {spreadsheet.title}")
    except Exception as e:
        log(f"Authentication Error: {e}")
        return

    # Expected tabs and headers (matching gsheets_handler.py tab names)
    expected_structure = {
        "Transactions": ["Date", "Account", "Category", "Subcategory", "Description", "Amount", "Type", "Status"],
        "Investments": ["Purchase Date", "Account", "Symbol", "Shares", "Avg Buy Price", "Current Price", "Total Value (USD)", "Total Value (IDR)", "Realized P/L"],
        "Categories": ["Category", "Subcategory", "Type"],
        "Accounts": ["Account Name", "Currency", "Balance", "Type"],
        "Budgets": ["Category", "Monthly Budget", "Effective From"]
    }

    worksheets = spreadsheet.worksheets()
    existing_tabs = {ws.title: ws for ws in worksheets}
    
    all_passed = True
    log("\nVerifying Tabs and Headers:")
    
    for tab_name, expected_headers in expected_structure.items():
        if tab_name in existing_tabs:
            log(f"[OK] Tab '{tab_name}' exists.")
            # Check headers
            try:
                actual_headers = existing_tabs[tab_name].row_values(1)
                missing_headers = [h for h in expected_headers if h not in actual_headers]
                if not missing_headers:
                    log(f"    [OK] Headers are correct: {actual_headers}")
                else:
                    log(f"    [FAIL] Missing headers: {missing_headers}")
                    log(f"        Actual headers: {actual_headers}")
                    all_passed = False
            except Exception as e:
                log(f"    [FAIL] Error reading headers: {e}")
                all_passed = False
        else:
            log(f"[FAIL] Tab '{tab_name}' is missing.")
            all_passed = False

    if all_passed:
        log("\nVerification PASSED: All required tabs and headers are correctly set up.")
    else:
        log("\nVerification FAILED: Please check the missing tabs or headers.")

    with open("verification_results.log", "w") as f:
        f.write("\n".join(results))

if __name__ == "__main__":
    verify_gsheet()
