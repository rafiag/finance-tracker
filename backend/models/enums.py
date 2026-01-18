from enum import Enum

class TransactionType(str, Enum):
    EXPENSE = "Expense"
    INCOME = "Income"
    TRANSFER = "Transfer"
    ASSET = "Asset"
    TRADE_BUY = "Trade_Buy"
    TRADE_SELL = "Trade_Sell"

class TransactionStatus(str, Enum):
    NORMAL = "Normal"
    FLAGGED = "Flagged"

class Currency(str, Enum):
    IDR = "IDR"
    USD = "USD"
