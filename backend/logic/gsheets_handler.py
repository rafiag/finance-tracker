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
    TAB_CATEGORIES = 'Categories'
    TAB_ACCOUNTS = 'Accounts'
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
        Fetch all valid categories from Categories tab.
        
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
            List of dicts with keys: name, currency, balance, type
        """
        self.connect()
        worksheet = self._spreadsheet.worksheet(self.TAB_ACCOUNTS)
        records = worksheet.get_all_records()

        return [
            {
                'name': row.get('Account Name', ''),
                'currency': row.get('Currency', ''),
                'balance': float(row.get('Balance', 0) or 0),
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
                'purchase_date': row.get('Purchase Date', ''),
                'account': row.get('Account', ''),
                'symbol': row.get('Symbol', ''),
                'shares': float(row.get('Shares', 0) or 0),
                'avg_price': float(row.get('Avg Buy Price', 0) or 0),
                'current_price': float(row.get('Current Price', 0) or 0),
                'total_value': float(row.get('Total Value', 0) or 0),
                'realized_pl': float(row.get('Realized P/L', 0) or 0)
            }
            for row in records
            if row.get('Symbol')
        ]

    def update_investment(
        self,
        symbol: str,
        shares_change: float,
        price: float,
        realized_pl: float = 0,
        account: str = "",
        purchase_date: str = ""
    ) -> None:
        """
        Update or create an investment record.

        Columns: Purchase Date | Account | Symbol | Shares | Avg Buy Price | Current Price | Total Value | Realized P/L
        """
        self.connect()
        worksheet = self._spreadsheet.worksheet(self.TAB_INVESTMENTS)
        records = worksheet.get_all_records()

        found = False
        for i, row in enumerate(records, start=2):  # start=2 for 1-based index + header
            if row.get('Symbol') == symbol:
                current_shares = float(row.get('Shares', 0) or 0)
                current_avg = float(row.get('Avg Buy Price', 0) or 0)
                new_shares = current_shares + shares_change

                if shares_change > 0:  # Buying
                    if new_shares > 0:
                        new_avg = ((current_shares * current_avg) + (shares_change * price)) / new_shares
                    else:
                        new_avg = price
                else:  # Selling (avg price stays the same, realized profit tracked separately)
                    new_avg = current_avg

                new_pl = float(row.get('Realized P/L', 0) or 0) + realized_pl

                # Update columns D through H (Shares, Avg Buy Price, Current Price, Total Value, Realized P/L)
                worksheet.update(f'D{i}:H{i}', [[
                    new_shares,
                    new_avg,
                    price,
                    new_shares * price,
                    new_pl
                ]])
                found = True
                break

        if not found and shares_change > 0:
            # New investment: Purchase Date | Account | Symbol | Shares | Avg Buy Price | Current Price | Total Value | Realized P/L
            from datetime import datetime
            if not purchase_date:
                purchase_date = datetime.now().strftime("%Y-%m-%d")
            worksheet.append_row([
                purchase_date,
                account,
                symbol,
                shares_change,
                price,
                price,
                shares_change * price,
                0
            ], value_input_option='USER_ENTERED')

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

    def get_transactions(self, year: int = None, month: int = None) -> list[dict]:
        """
        Fetch all transactions, optionally filtered by year and month.

        Returns:
            List of transaction dicts with all fields.
        """
        self.connect()
        worksheet = self._spreadsheet.worksheet(self.TAB_TRANSACTIONS)
        records = worksheet.get_all_records()

        transactions = []
        for row in records:
            date_str = row.get('Date', '')
            if not date_str:
                continue

            # Parse date for filtering
            try:
                from datetime import datetime
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                if year and date_obj.year != year:
                    continue
                if month and date_obj.month != month:
                    continue
            except ValueError:
                pass  # Keep transactions with unparseable dates

            transactions.append({
                'date': date_str,
                'account': row.get('Account', ''),
                'category': row.get('Category', ''),
                'subcategory': row.get('Subcategory', ''),
                'description': row.get('Description', ''),
                'amount': float(row.get('Amount', 0) or 0),
                'type': row.get('Type', ''),
                'status': row.get('Status', 'Normal')
            })

        return transactions

    def get_budgets(self) -> list[dict]:
        """Fetch all budget records."""
        self.connect()
        worksheet = self._spreadsheet.worksheet(self.TAB_BUDGETS)
        records = worksheet.get_all_records()

        return [
            {
                'category': row.get('Category', ''),
                'monthly_budget': float(row.get('Monthly Budget', 0) or 0),
                'effective_from': row.get('Effective From', '')
            }
            for row in records
            if row.get('Category')
        ]

    def update_transaction(self, row_index: int, data: dict) -> bool:
        """
        Update a transaction at a specific row.

        Args:
            row_index: 1-based row index (including header, so row 2 is first data row)
            data: Dict with transaction fields to update
        """
        self.connect()
        worksheet = self._spreadsheet.worksheet(self.TAB_TRANSACTIONS)

        row = [
            data.get('date', ''),
            data.get('account', ''),
            data.get('category', ''),
            data.get('subcategory', ''),
            data.get('description', ''),
            data.get('amount', 0),
            data.get('type', ''),
            data.get('status', 'Normal')
        ]

        worksheet.update(f'A{row_index}:H{row_index}', [row], value_input_option='USER_ENTERED')
        return True

    def delete_transaction(self, row_index: int) -> bool:
        """
        Delete a transaction at a specific row.

        Args:
            row_index: 1-based row index
        """
        self.connect()
        worksheet = self._spreadsheet.worksheet(self.TAB_TRANSACTIONS)
        worksheet.delete_rows(row_index)
        return True


# Singleton instance for reuse
_handler: Optional[GoogleSheetsHandler] = None


def get_sheets_handler() -> GoogleSheetsHandler:
    """Get the singleton GoogleSheetsHandler instance."""
    global _handler
    if _handler is None:
        _handler = GoogleSheetsHandler()
    return _handler
