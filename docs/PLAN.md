# Project: AI-Powered Telegram Finance Tracker (Monsy Inspired)

## 1. Project Overview
An automated system to track personal expenses and income via Telegram, featuring a modern dashboard inspired by Monsy.app.
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
5. **Next.js Dashboard (Monsy-Style UI):**
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
- **`Transactions`**: `Date | Account | Category | Subcategory | Description | Amount | Type (Inc/Exp/Transfer/Asset) | Status (normal/flagged)`.
  - *Note: For transfers, the Description field notes the counter account (e.g., "Transfer to RDN"). Two rows are created: one debit from source account, one credit to destination account.*
- **`Investments`**: `Purchase Date | Account | Symbol | Shares | Avg Buy Price | Currency | Total Value (USD) | Total Value (IDR) | Realized P/L`.
- **`Categories`**: `Category | Subcategory | Type (Income/Expense/Transfer/Investment)`.
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
- [ ] **Market Data Service:** (Phase 4) Integrate a light service (e.g., `yfinance` or a simple web scraper) to update `Current Price` in the `Investments` tab for real-time P/L calculation on the dashboard.

---

### Phase 4: Monsy-Inspired Dashboard (Next.js)
- [ ] **Project Setup:**
    - Initialize Next.js 14+ with App Router, TypeScript, and Tailwind CSS.
    - Install shadcn/ui components (Card, Button, Table, Dialog, Select, etc.).
    - Install Recharts for data visualizations.
- [ ] **Design System & Layout:**
    - Implement Tailwind config for Monsy color palette (Teal for income, Red for expenses).
    - Custom CSS for premium look (rounded corners, soft shadows, glassmorphism).
    - Responsive sidebar navigation: **Dashboard**, **Assets**, **Budget**, **Expenses**, **Transfer**, **Transactions**.
    - Year/Month global filters at the top right of the application.
- [ ] **Dashboard Overview:**
    - **Income Card**: Main focus card showing total income, donut chart breakdown of sources, and % change.
    - **Quick Summary**: Small cards for "Total Saving" and "Total Expenses" with trend indicators.
    - **Account Balances**: Side scrollable or list of current bank/e-wallet account states.
    - **Expense Activity**: Interactive daily area chart showing spending trends for the selected month.
- [ ] **Expenses Page:**
    - **Expenses Distribution**: Donut chart showing category-wise expense breakdown.
    - **Category Breakdown Table**: List of expense categories with amounts and percentages.
    - **Date Range Filter**: Filter expenses by month/custom date range.
- [ ] **Assets & Portfolio Page:**
    - **Net Worth Overview**: Area chart showing net worth growth over time.
    - **Balances Breakdown**: Donut chart and legend for Assets vs. Transaction accounts.
    - **Overall Balances Table**: Detailed list showing Account, Type, Current Balance, In/Out flows.
    - **Stock Holdings Table**: Comprehensive view including Account, Symbol, Shares, Avg. Buy Price, Purchase Date, Current Price (Market), Total Market Value, and Potential P/L (Color-coded).
- [ ] **Budget & Transaction Management:**
    - **Budget Progress**: Card-based summary with category progress bars, "Safe" vs. "Over Budget" badges.
    - **Transactions Table**: Searchable, filterable list with capability to edit/delete records.
    - **Review Queue**: Flagged transactions (low AI confidence) displayed for manual category/account verification.
- [ ] **Add Record Modals:**
    - **Add Expense**: Date, Account, Category, Subcategory, Amount, Description fields.
    - **Add Income**: Date, Account, Category, Amount, Description fields.
    - **Add Transfer**: From Account, To Account, Amount, Date fields.
    - **Add Stock**: Symbol, Shares, Purchase Price, Purchase Date fields.

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
├── backend/
│   ├── main.py                # FastAPI (Telegram Webhook + API)
│   ├── logic/
│   │   ├── gsheets_handler.py # GSheets CRUD
│   │   ├── ai_processor.py    # Gemini Logic & OCR
│   │   └── telegram_utils.py  # Telegram API Helpers
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── app/                   # Next.js App Router pages
│   │   ├── layout.tsx         # Root layout with sidebar
│   │   ├── page.tsx           # Dashboard (home)
│   │   ├── assets/
│   │   ├── budget/
│   │   ├── expenses/
│   │   ├── transactions/
│   │   └── settings/
│   ├── components/            # Reusable UI components
│   │   ├── ui/                # shadcn/ui components
│   │   ├── charts/            # Recharts wrappers
│   │   └── modals/            # Add Record modals
│   ├── lib/                   # API client, utilities
│   ├── tailwind.config.ts
│   ├── package.json
│   └── Dockerfile
└── docker-compose.yml         # Local dev orchestration
```