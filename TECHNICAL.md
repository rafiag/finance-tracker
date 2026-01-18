# Technical Documentation

This document contains technical details for developers working on the Finance Tracker project.

## Architecture Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Telegram Bot  │────▶│  FastAPI Backend │────▶│  Google Sheets  │
│   (User Input)  │     │  (Processing)    │     │  (Database)     │
└─────────────────┘     └────────┬────────┘     └─────────────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │   Gemini AI     │
                        │   (LLM/OCR)     │
                        └─────────────────┘
```

## Technology Stack

| Component | Technology | Version |
|-----------|------------|---------|
| Backend Framework | FastAPI | 0.109.2 |
| ASGI Server | Uvicorn | 0.27.1 |
| AI/LLM | Google Gemini 2.0 Flash | latest |
| Database | Google Sheets API | v4 |
| Sheets Client | gspread | 6.0.2 |
| HTTP Client | httpx | 0.26.0 |
| Validation | Pydantic | 2.6.1 |

## Project Structure

```
backend/
├── main.py                    # FastAPI application & endpoints
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Container configuration
├── .env                       # Environment variables (not committed)
├── credentials.json           # Google service account (not committed)
├── logic/
│   ├── __init__.py
│   ├── gsheets_handler.py     # Google Sheets CRUD operations
│   ├── ai_processor.py        # Gemini AI integration
│   └── telegram_utils.py      # Telegram Bot API helpers
└── scripts/
    ├── populate_dummy_data.py # Generate test data
    └── verify_sheets.py       # Verify sheet structure
```

## Google Sheets Schema

### Transactions Tab
| Column | Type | Description |
|--------|------|-------------|
| Date | String | YYYY-MM-DD format |
| Account | String | Source account name |
| Category | String | Main category |
| Subcategory | String | Subcategory |
| Description | String | Transaction note |
| Amount | Number | Amount in IDR (Global Standard) |
| Type | String | Expense/Income/Transfer/Asset |
| Status | String | Normal/Flagged |

### Investments Tab
| Column | Type | Description |
|--------|------|-------------|
| Purchase Date | String | YYYY-MM-DD format |
| Account | String | Investment account |
| Symbol | String | Stock ticker |
| Shares | Number | Number of shares |
| Avg Buy Price | Number | Average purchase price |
| Total Value (USD) | Number | Value in USD (Null for IDR assets) |
| Total Value (IDR) | Number | Value in IDR |
| Realized P/L | Number | Realized profit/loss |

### Categories Tab
| Column | Type | Description |
|--------|------|-------------|
| Category | String | Main category name |
| Subcategory | String | Subcategory name |
| Type | String | Expense/Income/Transfer/Investment |

### Settings_Accounts Tab
| Column | Type | Description |
|--------|------|-------------|
| Account Name | String | Account identifier |
| Currency | String | Currency code (IDR) |
| Balance | Number/Formula | Current balance (use SUMIFS formula for auto-calculation) |
| Type | String | Bank/Cash/Investment/RDN |

**Recommended Balance Formula** (put in Balance column, e.g., C2):
```
=SUMIFS(Transactions!F:F, Transactions!B:B, A2, Transactions!G:G, "Income")
-SUMIFS(Transactions!F:F, Transactions!B:B, A2, Transactions!G:G, "Expense")
-SUMIFS(Transactions!F:F, Transactions!B:B, A2, Transactions!G:G, "Asset")
+SUMIFS(Transactions!F:F, Transactions!B:B, A2, Transactions!G:G, "Transfer", Transactions!E:E, "Transfer from*")
-SUMIFS(Transactions!F:F, Transactions!B:B, A2, Transactions!G:G, "Transfer", Transactions!E:E, "Transfer to*")
```

### Budgets Tab
| Column | Type | Description |
|--------|------|-------------|
| Category | String | Category name |
| Monthly Budget | Number | Budget amount |
| Effective From | String | Start date |

## API Endpoints

### Telegram Webhook
- `POST /webhook/telegram` - Receives Telegram updates

### Dashboard APIs - Data Fetching
- `GET /api/transactions` - List transactions (optional: ?year=&month=)
- `GET /api/investments` - List investment holdings
- `GET /api/categories` - List categories
- `GET /api/accounts` - List accounts
- `GET /api/budgets` - List budgets
- `GET /api/summary` - Financial summary with category breakdowns (optional: ?year=&month=)
- `GET /api/account-balances` - Account balances with inflow/outflow (optional: ?year=&month=)
- `GET /api/daily-expenses` - Daily expense totals for charts (optional: ?year=&month=)
- `GET /api/budget-progress` - Budget vs actual spending per category (optional: ?year=&month=)

### Dashboard APIs - Data Creation
- `POST /api/transactions` - Create expense/income transaction
- `POST /api/transfers` - Create transfer between accounts
- `POST /api/investments` - Create stock purchase
- `PUT /api/transactions/{row_index}` - Update transaction
- `DELETE /api/transactions/{row_index}` - Delete transaction

### Health Checks
- `GET /` - Basic health check
- `GET /health` - Detailed health check

### Development
- `POST /test/transaction` - Test transaction processing

## Transaction Processing Flow

1. **Message Received**: Telegram webhook receives update
2. **Authorization**: Check if sender matches authorized chat ID
3. **Content Extraction**: Extract text and/or photo from message
4. **Context Loading**: Fetch categories, accounts, and portfolio from Sheets
5. **AI Processing**: Send to Gemini with context for parsing
6. **Transaction Creation**:
   - Regular (Expense/Income): Single row appended
   - Transfer: Two rows (debit source, credit destination)
   - Trade_Buy: Asset transaction + portfolio update
   - Trade_Sell: Two transactions (Return of Capital + Capital Gain) + portfolio update
7. **Confirmation**: Send formatted message back to user

## Investment Handling

### Buy Flow
1. Create Asset-type transaction (debit from account)
2. Update Investments sheet:
   - If symbol exists: Recalculate average price
   - If new symbol: Create new row

### Sell Flow
1. Look up average buy price from portfolio
2. Calculate base cost (shares × avg price)
3. Calculate capital gain (sale amount - base cost)
4. Create two transactions:
   - Return of Capital (Asset type): base cost
   - Capital Gain (Income type): profit/loss
5. Update Investments sheet (reduce shares, add to realized P/L)

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| TELEGRAM_BOT_TOKEN | Yes | Bot token from BotFather |
| MY_TELEGRAM_CHAT_ID | Yes | Authorized user's chat ID |
| GEMINI_API_KEY | Yes | Google AI Studio API key |
| GOOGLE_SHEET_ID | Yes | Target spreadsheet ID |
| GOOGLE_SHEETS_CREDENTIALS_PATH | No | Path to credentials.json (default: ./credentials.json) |
| GOOGLE_SHEETS_CREDENTIALS_JSON | No | JSON string of credentials (for Railway) |
| FRONTEND_URL | No | Dashboard URL for CORS |
| PORT | No | Server port (default: 8000) |

## Credential Priority

1. Streamlit secrets (for Streamlit Cloud)
2. `GOOGLE_SHEETS_CREDENTIALS_JSON` environment variable
3. `credentials.json` file path

## AI Prompt Design

The AI processor uses a structured prompt that includes:
- Current date for context
- Valid categories and subcategories
- Valid account names
- Current investment portfolio
- Rules for amount parsing (Indonesian Rupiah formats)
- Rules for transaction type detection
- JSON output format specification

## Error Handling

- Rate limits: Exponential backoff (2s → 4s → 8s) for Gemini API
- Parse failures: Transaction flagged with error message
- Webhook errors: Return 200 status (Telegram requirement)
- User errors: Friendly message sent via Telegram

## Security Measures

- Authorization: Only configured chat ID can trigger transactions
- CORS: Restricted to localhost and configured frontend URL
- Credentials: Not committed to repository
- Input validation: All user input validated before processing

## Docker Configuration

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Development Commands

```bash
# Start containers
docker compose up -d

# Rebuild after dependency changes
docker compose up -d --build

# View logs
docker compose logs -f backend

# Run scripts
docker compose exec backend python scripts/verify_sheets.py
docker compose exec backend python scripts/populate_dummy_data.py
```

## Known Limitations

1. **Single User**: System designed for single authorized user
2. **Row-Based Updates**: Transaction updates use row index (no unique IDs)
3. **No Real-Time Prices**: Investment prices require manual/scheduled updates
4. **Rate Limits**: Gemini API has usage limits
5. **Google Sheets Limits**: 500 requests per 100 seconds per project

## Future Enhancements

- [ ] Market data service for real-time stock prices (Phase 4)
- [ ] Dashboard authentication (Phase 5)
- [ ] Scheduled budget alerts via Telegram
- [ ] Transaction unique IDs for reliable updates/deletes
