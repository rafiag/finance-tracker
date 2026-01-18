# Project: AI-Powered Telegram Finance Tracker

## 1. Project Overview
An automated system to track personal expenses and income via Telegram, featuring a modern dashboard with AI processing.
- **Input:** Text or Images (Invoices/Receipts) sent to Telegram.
- **Processing:** Python (FastAPI) + Gemini 1.5 Flash (LLM).
- **Storage:** Google Sheets (Relational Database structure).
- **Dashboard:** Next.js + Tailwind CSS + shadcn/ui (Card-based, Teal/Red theme).
- **Hosting:** Railway for 24/7 uptime.

---

## 2. Technical Architecture & Design
1. **Telegram Bot:** Receives message -> Webhook to FastAPI.
2. **FastAPI (Backend):** 
    - Downloads image/text from Telegram.
    - Fetches current Categories/Subcategories/Accounts from GSheets.
    - Sends data to Gemini for structured extraction & OCR.
    - Appends data to GSheets. (Images are processed and discarded, not stored).
3. **Gemini 1.5 Flash:** Maps messy input to specific GSheet categories and subcategories. Handles complex receipt scanning.
4. **Google Sheets:** Stores Transactions, Categories/Subcategories, Accounts (Assets), and Budgets.
5. **Next.js Dashboard:**
    - **Sidebar Navigation:** Dashboard, Transactions, Budget, Assets, Settings.
    - **Card-Based Overview:** Large metrics for Income (Teal), Expenses (Red).
    - **Visualizations:** Recharts for Activity Line Chart, Category Distribution (Pie), and Budget Usage.
    - **Quick Actions:** "Add Transaction" modal via Dashboard (as a backup to Telegram).
    - **API Integration:** Fetch data from FastAPI backend via REST endpoints.

---

## 3. Detailed Phase Breakdown

### Phase 1: Environment & API Setup
- [x] **Google Cloud:** Create project, enable Sheets & Drive API. Download `service_account.json`.
- [x] **Telegram:** Create a bot via BotFather, get the API Token.
- [x] **Google AI Studio:** Get API Key for Gemini 1.5 Flash.
- [x] **Railway:** Link GitHub account and set up projects for FastAPI and Streamlit.

### Phase 2: Database Schema (Google Sheets)
Create Spreadsheet with:
- **`Transactions`**: `ID | Date | Account | Category | Subcategory | Description | Amount | Type (Inc/Exp/Transfer/Asset) | Status (normal/flagged)`.
  - *Note: For transfers, two rows are created:*
    - *Source account row: Subcategory = "Transfer-Out", Description = "Transfer to {destination}"*
    - *Destination account row: Subcategory = "Transfer-In", Description = "Transfer from {source}"*
- **`Investments`**: `Purchase Date | Account | Symbol | Shares | Avg Buy Price | Currency | Total Value (USD) | Total Value (IDR) | Realized P/L`.
- **`Categories`**: `Category | Subcategory | Type (Income/Expense/Transfer/Investment)`.
  - *Note: Transfer category has two subcategories: Transfer-In and Transfer-Out*
- **`Accounts`**: `Account Name | Currency | Balance | Type (Bank/Cash/Investment/RDN)`.
- **`Budgets`**: `Category | Monthly Budget | Effective From` (Category level only).

### Phase 3: Backend & AI Engine (FastAPI)
- [x] **Integration Layer:** POST /telegram for Bot Webhooks.
- [x] **AI Processor:**
    - System Prompt with dynamic Categories and Subcategories.
    - Multimodal OCR for receipts.
    - **Investment Logic:**
      - **Buy stocks**: Add row to Investments sheet with Account, Purchase Date, Symbol, Shares, Avg Buy Price. Create Transaction with Type=Asset (debit from account).
      - **Sell stocks**: Update existing Investments row (decrease Shares, update Realized P/L). Create TWO transactions:
        1. Return of Capital (Asset type): Original investment amount returned to account
        2. Capital Gain (Income type): Profit/loss from the sale
      - Handle fractional shares and FIFO/LIFO cost basis calculations.
    - **Review Flag:** When AI confidence is low, mark transaction with `needs_review: true` for manual verification on dashboard.
- [x] **GSheet Connector:** `gspread` for CRUD operations across all tabs.
- [x] **Dashboard API Endpoints:** REST endpoints for frontend data fetching (transactions, investments, categories, accounts, budgets, summary).

---

### Phase 4: Dashboard (Next.js)
> **Detailed Requirements:** See `docs/PHASE4_FRONTEND.md`

**Overview:**
Build a modern, premium web dashboard for visualizing and managing financial data.

**Core Pages:**
- [ ] **Dashboard Overview** - Income/expense summary, account balances, activity charts, pending review indicator
- [ ] **Assets & Portfolio** - Net worth tracking, transaction accounts table, stock holdings with real-time market data
- [ ] **Budget Management** - Current month budget progress, historical category performance
- [ ] **Transactions & Expenses** - Unified transaction table with edit/delete/approve functionality, expense distribution charts
- [ ] **Settings** - Manage accounts, categories/subcategories, and budget limits

**Key Features:**
- [ ] Unified "Add Record" quick action modal (Expense/Income/Transfer/Stock)
- [ ] Transaction edit/approval workflow for flagged and normal transactions
- [ ] Year/Month global filters (Dashboard and Transactions pages)
- [ ] Market data integration for real-time stock prices and P/L calculations
- [ ] Responsive design with modern aesthetic (Teal/Red color scheme)

**Tech Stack:**
- Next.js 14+ (App Router) + TypeScript + Tailwind CSS
- shadcn/ui components + Recharts for visualizations
- API integration with FastAPI backend (authenticated via API key)

### Phase 5: Deployment & Polish
- [ ] **Railway Configuration:**
    - Set up multi-service deployment: FastAPI (Bot/API) + Next.js (Dashboard).
    - Configure environment variables (Bot Token, Gemini API, GSheets credentials, API URL).
    - Set up persistent health checks and automated redeployment from GitHub.
- [ ] **Security & Access Control:**
    - Implement NextAuth.js or simple session-based authentication for the dashboard.
    - Ensure only specific Telegram user IDs can trigger the bot (already implemented).
- [ ] **Final Integration:**
    - Set the Telegram Bot Webhook to point to the FastAPI endpoint on Railway.
    - Verify end-to-end flow: Telegram message -> GSheet -> Dashboard update.
    - (Optional) Implement scheduled Telegram alerts for weekly budget reports.

---

## 4. The "Brain" (Gemini Strategy)
- **Context:** Valid Categories & Subcategories, Valid Accounts, Today's Date.
- **Rules:** Return JSON only. Map unknown categories to "Miscellaneous". Handle image data for OCR.
- **Hierarchical Mapping:** AI must accurately map to *both* Category and Subcategory.

---

## 5. File Structure
```text
project-root/
├── .agent/                    # Agent instructions and workflows
├── backend/
│   ├── logic/
│   │   ├── ai_processor.py    # Gemini Logic & OCR
│   │   ├── exchange_rate.py   # Currency conversion & valuation
│   │   ├── gsheets_handler.py # Google Sheets integration
│   │   └── telegram_utils.py  # Telegram bot utilities
│   ├── models/
│   │   ├── enums.py           # Enum definitions
│   │   └── schemas.py         # Pydantic data models
│   ├── routers/
│   │   ├── dashboard.py       # Dashboard API endpoints
│   │   ├── telegram.py        # Telegram webhook handler
│   │   └── transactions.py    # Transaction CRUD
│   ├── scripts/
│   │   ├── populate_dummy_data.py
│   │   └── verify_sheets.py
│   ├── dependencies.py        # Auth & Rate limiting
│   ├── main.py                # FastAPI Entry point
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── docs/
│   ├── reference/             # UI/UX design references
│   ├── BACKEND.md             # Backend architecture details
│   ├── BACKEND_CODE_REVIEW.md # Code quality tracking
│   ├── PHASE4_FRONTEND.md     # Frontend requirements & specifications
│   └── PLAN.md                # Project roadmap
├── frontend/                  # Next.js Dashboard
├── AGENTS.md                  # Collaboration guidelines
├── docker-compose.yml         # Container orchestration
└── README.md                  # Project overview
```
