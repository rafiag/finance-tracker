"""
Google Sheets Handler for Finance Tracker
Manages all interactions with the Finance Tracker Google Spreadsheet
"""

import os
from datetime import datetime
from typing import Optional

import gspread
from google.oauth2.service_account import Credentials


class GoogleSheetsHandler:
    """Handles all Google Sheets operations for the Finance Tracker."""
    
    # Define the scopes needed for Google Sheets and Drive access
    SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    
    # Sheet tab names
    TAB_TRANSACTIONS = 'Transactions'
    TAB_CATEGORIES = 'Settings_Categories'
    TAB_ACCOUNTS = 'Settings_Accounts'
    TAB_BUDGETS = 'Budgets'
    TAB_INVESTMENTS = 'Investments'
    
    def __init__(self):
        """Initialize the Google Sheets handler with credentials."""
        self._client: Optional[gspread.Client] = None
        self._spreadsheet: Optional[gspread.Spreadsheet] = None
        
    def _get_credentials(self) -> Credentials:
        """Get Google service account credentials."""
        import json

        # Priority 1: Check Streamlit secrets (for Streamlit Cloud deployment)
        try:
            import streamlit as st
            if hasattr(st, 'secrets') and 'GOOGLE_SHEETS_CREDENTIALS_JSON' in st.secrets:
                creds_json = st.secrets['GOOGLE_SHEETS_CREDENTIALS_JSON']
                creds_dict = json.loads(creds_json) if isinstance(creds_json, str) else dict(creds_json)
                return Credentials.from_service_account_info(creds_dict, scopes=self.SCOPES)
        except (ImportError, Exception):
            pass

        # Priority 2: Check environment variable (for Railway deployment)
        creds_json = os.getenv('GOOGLE_SHEETS_CREDENTIALS_JSON')
        if creds_json:
            creds_dict = json.loads(creds_json)
            return Credentials.from_service_account_info(creds_dict, scopes=self.SCOPES)

        # Priority 3: Use credentials file path (for local development)
        creds_path = os.getenv('GOOGLE_SHEETS_CREDENTIALS_PATH', './credentials.json')
        return Credentials.from_service_account_file(creds_path, scopes=self.SCOPES)
    
    def connect(self) -> None:
        """Establish connection to Google Sheets."""
        if self._client is None:
            creds = self._get_credentials()
            self._client = gspread.authorize(creds)

        if self._spreadsheet is None:
            sheet_id = self._get_sheet_id()
            if not sheet_id:
                raise ValueError("GOOGLE_SHEET_ID is not configured")
            self._spreadsheet = self._client.open_by_key(sheet_id)

    def _get_sheet_id(self) -> Optional[str]:
        """Get Google Sheet ID from secrets or environment."""
        # Priority 1: Check Streamlit secrets
        try:
            import streamlit as st
            if hasattr(st, 'secrets') and 'GOOGLE_SHEET_ID' in st.secrets:
                return st.secrets['GOOGLE_SHEET_ID']
        except (ImportError, Exception):
            pass

        # Priority 2: Check environment variable
        return os.getenv('GOOGLE_SHEET_ID')
    
    def get_categories(self) -> list[dict]:
        """
        Fetch all valid categories from Settings_Categories tab.
        
        Returns:
            List of dicts with keys: category, subcategory, type
        """
        self.connect()
        worksheet = self._spreadsheet.worksheet(self.TAB_CATEGORIES)
        records = worksheet.get_all_records()
        
        return [
            {
                'category': row.get('Category', ''),
                'subcategory': row.get('Subcategory', ''),
                'type': row.get('Type', '')
            }
            for row in records
            if row.get('Category')  # Skip empty rows
        ]
    
    def get_accounts(self) -> list[dict]:
        """
        Fetch all valid accounts from Settings_Accounts tab.
        
        Returns:
            List of dicts with keys: name, currency, type
        """
        self.connect()
        worksheet = self._spreadsheet.worksheet(self.TAB_ACCOUNTS)
        records = worksheet.get_all_records()
        
        return [
            {
                'name': row.get('Account Name', ''),
                'currency': row.get('Currency', ''),
                'type': row.get('Type', '')
            }
            for row in records
            if row.get('Account Name')  # Skip empty rows
        ]

    def get_investments(self) -> list[dict]:
        """Fetch all current investments."""
        self.connect()
        worksheet = self._spreadsheet.worksheet(self.TAB_INVESTMENTS)
        records = worksheet.get_all_records()
        return [
            {
                'symbol': row.get('Symbol', ''),
                'shares': float(row.get('Shares', 0)),
                'avg_price': float(row.get('Avg Buy Price', 0)),
                'current_price': float(row.get('Current Price', 0)),
                'total_value': float(row.get('Total Value', 0)),
                'realized_pl': float(row.get('Realized P/L', 0))
            }
            for row in records
            if row.get('Symbol')
        ]

    def update_investment(self, symbol: str, shares_change: float, price: float, realized_pl: float = 0) -> None:
        """Update or create an investment record."""
        self.connect()
        worksheet = self._spreadsheet.worksheet(self.TAB_INVESTMENTS)
        records = worksheet.get_all_records()
        
        found = False
        for i, row in enumerate(records, start=2):  # start=2 for 1-based index + header
            if row.get('Symbol') == symbol:
                current_shares = float(row.get('Shares', 0))
                current_avg = float(row.get('Avg Buy Price', 0))
                new_shares = current_shares + shares_change
                
                if shares_change > 0:  # Buying
                    new_avg = ((current_shares * current_avg) + (shares_change * price)) / new_shares
                else:  # Selling (avg price stays the same, realized profit tracked separately)
                    new_avg = current_avg
                    
                new_pl = float(row.get('Realized P/L', 0)) + realized_pl
                
                worksheet.update(f'B{i}:F{i}', [[
                    new_shares, 
                    new_avg, 
                    price, 
                    new_shares * price, 
                    new_pl
                ]])
                found = True
                break
        
        if not found and shares_change > 0:
            worksheet.append_row([
                symbol, 
                shares_change, 
                price, 
                price, 
                shares_change * price, 
                0
            ])

    def append_transaction(
        self,
        date: str,
        account: str,
        category: str,
        subcategory: str,
        note: str,
        amount: float,
        transaction_type: str,
        status: str = 'Normal'
    ) -> bool:
        """
        Append a new transaction to the Transactions tab.
        """
        self.connect()
        worksheet = self._spreadsheet.worksheet(self.TAB_TRANSACTIONS)
        
        row = [
            date,
            account,
            category,
            subcategory,
            note,
            amount,
            transaction_type,
            status
        ]
        
        worksheet.append_row(row, value_input_option='USER_ENTERED')
        return True
    
    def get_category_list_for_prompt(self) -> str:
        """
        Get a formatted string of categories for the AI prompt.
        
        Returns:
            Formatted string listing all valid categories
        """
        categories = self.get_categories()
        
        # Group by category
        grouped: dict[str, list[str]] = {}
        for cat in categories:
            main_cat = cat['category']
            sub_cat = cat['subcategory']
            if main_cat not in grouped:
                grouped[main_cat] = []
            grouped[main_cat].append(f"{sub_cat} ({cat['type']})")
        
        # Format as readable string
        lines = []
        for main_cat, subcats in grouped.items():
            lines.append(f"- {main_cat}: {', '.join(subcats)}")
        
        return "\n".join(lines)
    
    def get_account_list_for_prompt(self) -> str:
        """
        Get a formatted string of accounts for the AI prompt.
        """
        accounts = self.get_accounts()
        
        lines = []
        for acc in accounts:
            lines.append(f"- {acc['name']} ({acc['type']})")
        
        return "\n".join(lines)

    def get_investment_list_for_prompt(self) -> str:
        """Get current portfolio as a string for context."""
        investments = self.get_investments()
        lines = []
        for inv in investments:
            lines.append(f"- {inv['symbol']}: {inv['shares']} shares @ avg Rp {inv['avg_price']:,.0f}".replace(",", "."))
        return "\n".join(lines)
    
    def is_valid_category(self, category: str, subcategory: str) -> bool:
        """Check if a category/subcategory combination exists."""
        categories = self.get_categories()
        for cat in categories:
            if cat['category'].lower() == category.lower() and \
               cat['subcategory'].lower() == subcategory.lower():
                return True
        return False
    
    def is_valid_account(self, account: str) -> bool:
        """Check if an account name exists."""
        accounts = self.get_accounts()
        for acc in accounts:
            if acc['name'].lower() == account.lower():
                return True
        return False


# Singleton instance for reuse
_handler: Optional[GoogleSheetsHandler] = None


def get_sheets_handler() -> GoogleSheetsHandler:
    """Get the singleton GoogleSheetsHandler instance."""
    global _handler
    if _handler is None:
        _handler = GoogleSheetsHandler()
    return _handler
