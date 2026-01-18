# Phase 4: Frontend Dashboard - Detailed Requirements

> **Project:** AI-Powered Telegram Finance Tracker  
> **Phase:** 4 - Dashboard (Next.js)  
> **Last Updated:** 2026-01-18

---

## Table of Contents

1. [Tech Stack & Setup](#1-tech-stack--setup)
2. [Design System](#2-design-system)
3. [Navigation & Layout](#3-navigation--layout)
4. [Pages & Features](#4-pages--features)
5. [Shared Components](#5-shared-components)
6. [API Integration](#6-api-integration)
7. [Acceptance Criteria](#7-acceptance-criteria)

---

## 1. Tech Stack & Setup

### 1.1 Technology Stack
- **Framework:** Next.js 14+ with App Router
- **Language:** TypeScript
- **Styling:** Tailwind CSS
- **UI Components:** shadcn/ui (Card, Button, Table, Dialog, Select, Input, Badge, etc.)
- **Charts:** Recharts
- **State Management:** React Context API / Zustand (TBD)
- **HTTP Client:** Fetch API / Axios

### 1.2 Project Initialization
```bash
npx create-next-app@latest frontend --typescript --tailwind --app
cd frontend
npx shadcn-ui@latest init
npx shadcn-ui@latest add card button table dialog select input badge tabs
npm install recharts
```

### 1.3 Environment Variables
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_API_KEY=your-dashboard-api-key
```

---

## 2. Design System

### 2.1 Color Palette
```js
// tailwind.config.js
theme: {
  extend: {
    colors: {
      income: {
        50: '#f0fdfa',
        500: '#14b8a6',  // Teal for income
        600: '#0d9488',
      },
      expense: {
        50: '#fef2f2',
        500: '#ef4444',  // Red for expenses
        600: '#dc2626',
      },
      neutral: {
        800: '#1f2937',
        900: '#111827',
      }
    }
  }
}
```

### 2.2 Visual Design Principles
- **Premium Look:** Soft shadows, rounded corners (8-12px), glassmorphism effects
- **Modern Typography:** Use Google Fonts (Inter/Outfit) for clean, professional appearance
- **Micro-animations:** Smooth hover effects, transitions (200-300ms)
- **Responsive:** Mobile-first approach, breakpoints at sm/md/lg/xl
- **Dark Mode:** Optional, use Tailwind's dark mode if time permits

### 2.3 Design Reference
- **Reference Screenshots:** `docs/reference/*.jpg`
- **Note:** Use screenshots as inspiration, not exact replicas. Adapt to modern web standards.

---

## 3. Navigation & Layout

### 3.1 Application Structure
```
┌─────────────────────────────────────────┐
│ Header: Logo | Filter                   │
├──────────┬──────────────────────────────┤
│          │                              │
│ Sidebar  │      Main Content Area       │
│ Menu     │                              │
│ ------   │                              │
│ Quick    │                              │
│ Action   │                              │
└──────────┴──────────────────────────────┘
```

### 3.2 Sidebar Navigation
**Fixed left sidebar with the following menu items:**
1. 📊 **Dashboard** - Overview page
2. 💼 **Assets** - Portfolio & account balances
3. 📈 **Budget** - Budget tracking & historical performance
4. 📝 **Transactions** - Combined transactions & expenses view
5. ⚙️ **Settings** - Manage accounts, categories, budgets

**Quick Action Button:**
- **Position:** Below the menu items, within the sidebar
- **Label:** "+ Add Transaction" or just "+" icon with tooltip
- **Action:** Opens the Quick Action Modal (see section 3.4)
- **Style:** Prominent button with accent color, full width or centered

**Notes:**
- Active page highlighted with accent color
- Icons for each menu item
- Collapsed/expanded states for mobile

### 3.3 Global Header
**Components:**
- **Left:** App logo/name
- **Right:** Year/Month filter (where applicable)

### 3.4 Quick Action Modal
**Unified "Add Record" modal with type selection:**
- **Type Selector Tabs:** Expense | Income | Transfer | Stock
- **Dynamic Fields** based on selected type:

| Type | Fields |
|------|--------|
| **Expense** | Date, Account, Category, Subcategory, Amount, Description |
| **Income** | Date, Account, Category, Amount, Description |
| **Transfer** | Date, From Account, To Account, Amount |
| **Stock** | Date, Account (Investment), Symbol, Shares, Purchase Price |

**Access Points:**
1. Sidebar Quick Action button ("+ Add Transaction")
2. Page-specific "Add" buttons (e.g., "+ Add Stock" on Assets page opens modal with Stock tab pre-selected)

---

## 4. Pages & Features

### 4.1 Dashboard Overview
**Reference:** `docs/reference/dashboard-*.jpg`

**Layout Sections:**

#### 4.1.1 Income Card (Hero Section)
- **Position:** Top left, largest card
- **Content:**
  - Total income for selected period (large number)
  - Donut chart showing income source breakdown
  - % change from previous period (green/red indicator)

#### 4.1.2 Quick Summary Cards
- **Total Saving** card (Income - Expenses)
  - Trend indicator (↑↓ with %)
- **Total Expenses** card
  - Trend indicator

#### 4.1.3 Account Balances Widget
- **Layout:** Horizontal scrollable list or vertical list
- **Content:** Current balance for each account (Bank/Cash/E-wallet)
- **Visual:** Account icon + name + balance

#### 4.1.4 Expense Activity Chart
- **Type:** Interactive daily area chart
- **X-axis:** Days of the month
- **Y-axis:** Spending amount
- **Features:**
  - Hover tooltips showing exact amounts
  - Highlight current day
  - Smoothed curve for visual appeal

#### 4.1.5 Pending Review Indicator
- **Placement:** Top right corner or near header
- **Visual:** Badge with count (e.g., "🔔 5 Flagged Transactions")
- **Action:** Click to navigate to Transactions page with "Flagged" filter applied

**Filters:**
- ✅ Year/Month selector (top right)

---

### 4.2 Assets & Portfolio Page
**Reference:** `docs/reference/asset-*.jpg`

**Layout Sections:**

#### 4.2.1 Net Worth Overview
- **Chart:** Area chart showing net worth growth over time
- **Calculation:** Sum of all account balances + investment values
- **Time Range:** Last 6 months / 1 year (toggle)

#### 4.2.2 Account Type Breakdown
**Two separate sections:**

##### A. Transaction Accounts
**Reference:** `docs/reference/asset-tracker.jpg`
- **Table Columns:** Account Name | Type | Current Balance | In (Month) | Out (Month)
- **Types:** Bank, Cash, E-wallet
- **Visual:** Donut chart showing distribution

##### B. Investment Accounts
**Reference:** `docs/reference/asset-details.jpg`
- **Stock Holdings Table:**
  - Columns: Account | Symbol | Shares | Avg. Buy Price | Purchase Date | Current Price* | Total Market Value* | P/L* | P/L %*
  - *Columns marked with asterisk require market data integration
- **Color Coding:** 
  - Green text/background for positive P/L
  - Red text/background for negative P/L
- **Totals Row:** Sum of all positions

#### 4.2.3 Market Data Integration
**Implementation:**
- **Service:** Use `yfinance` Python library (backend) or client-side API
- **Backend Endpoint:** `GET /api/market-data?symbols=AAPL,GOOGL`
- **Response:**
  ```json
  {
    "AAPL": {"price": 150.25, "change_percent": 1.5},
    "GOOGL": {"price": 2800.50, "change_percent": -0.3}
  }
  ```
- **Update Frequency:** 
  - Fetch on page load
  - Optional: Auto-refresh every 5 minutes
  - Cache with 5-minute TTL

**Filters:**
- ❌ No global filters (always shows current state)

**Actions:**
- "+ Add Stock" button (opens Quick Action modal with Stock tab)

---

### 4.3 Budget Management Page
**Reference:** `docs/reference/budgets-*.jpg`

**Layout Sections:**

#### 4.3.1 Current Month Budget Overview
- **Card-based layout** with one card per category
- **Each Card Shows:**
  - Category name
  - Progress bar (spent / budget limit)
  - Percentage used
  - Badge: "Safe" (green) if < 80% | "Warning" (yellow) if 80-100% | "Over Budget" (red) if > 100%

#### 4.3.2 Historical Budget Performance
- **Section Title:** "Category Performance Over Time"
- **Layout:** Table or card grid
- **Columns/Data:**
  - Category | Last 3 Months (bar charts) | Average Spending | Budget Limit
- **Visual:** Sparkline charts showing monthly trends

**Filters:**
- ❌ No global filters (current month + historical data is pre-determined)

**Actions:**
- "Edit Budgets" button (navigates to Settings page)

---

### 4.4 Transactions & Expenses Page
**Reference:** `docs/reference/transactions.jpg`, `docs/reference/transaction-add-expense.jpg`

**Note:** This is a **combined page** showing both transactions and expense-specific views.

#### 4.4.1 Transactions Table
**Columns:**
- Date | Account | Category | Subcategory | Description | Amount | Type | Status | Actions

**Features:**
- **Searchable:** Text search across description/category
- **Filterable:** 
  - Date range picker
  - Account multi-select
  - Category/Subcategory multi-select
  - Type filter (Income/Expense/Transfer/Asset)
  - Status filter (Normal/Flagged)
- **Sortable:** Click column headers to sort
- **Pagination:** 20 rows per page

**Visual Indicators:**
- **Flagged Badge:** Yellow/orange badge on "Status" column for flagged transactions
- **Type Color Coding:**
  - Income: Green text
  - Expense: Red text
  - Transfer: Blue text
  - Asset: Purple text

#### 4.4.2 Transaction Actions (All Transactions)
**For each row, provide action buttons:**

1. **Edit (✏️):**
   - Opens inline edit mode or modal
   - Editable Fields: Date, Account, Category, Subcategory, Description, Amount
   - "Save" button commits changes via `PUT /api/transactions/{id}`

2. **Delete (🗑️):**
   - Confirmation dialog: "Are you sure you want to delete this transaction?"
   - On confirm: `DELETE /api/transactions/{id}`

3. **Approve (✓):** (Only visible for flagged transactions)
   - Removes "Flagged" status (sets Status = "Normal")
   - Updates via `PUT /api/transactions/{id}` with `status: "Normal"`
   - Badge disappears after approval

#### 4.4.3 Expense Distribution Section
**Placement:** Above or beside the table
- **Donut Chart:** Category-wise expense breakdown for selected period
- **Legend:** Category names with amounts and percentages

**Filters:**
- ✅ Date range, Account, Category filters (shared with table)

**Actions:**
- "+ Add Expense" button (opens Quick Action modal with Expense tab)

---

### 4.5 Settings Page
**New page for managing core data entities**

#### 4.5.1 Accounts Management
**Table View:**
- Columns: Account Name | Type | Currency | Current Balance | Actions
- **Actions:**
  - Edit (modify name, type)
  - Delete (with validation - prevent deletion if transactions exist)
  - Add New Account (modal/form)

#### 4.5.2 Categories & Subcategories Management
**Hierarchical View:**
- **Income Categories** (expandable)
  - Subcategory 1
  - Subcategory 2
  - + Add Subcategory
- **Expense Categories** (expandable)
  - ...
- **Actions:**
  - Edit category/subcategory name
  - Delete (with validation)
  - Add New Category/Subcategory

#### 4.5.3 Budget Settings
**Form/Table Hybrid:**
- **For each expense category:**
  - Input field for monthly budget limit
  - "Effective From" date picker
- **Save All** button at bottom

**Filters:**
- ❌ No filters

---

## 5. Shared Components

### 5.1 Filter Bar Component
**Reusable filter component for applicable pages**

**Props:**
- `showDateRange: boolean`
- `showAccountFilter: boolean`
- `showCategoryFilter: boolean`
- `showTypeFilter: boolean`
- `onFilterChange: (filters) => void`

**UI:**
- Horizontal bar with filter dropdowns/pickers
- "Reset Filters" button
- Active filter count indicator

### 5.2 Transaction Edit Modal
**Reusable modal for editing transactions**

**Props:**
- `transaction: Transaction`
- `onSave: (updatedTransaction) => void`
- `onCancel: () => void`

**Features:**
- Form validation (required fields, amount > 0)
- Dynamic category/subcategory dropdown based on type
- "Approve" checkbox (if flagged)

### 5.3 Stat Card Component
**Reusable card for metrics**

**Props:**
- `title: string`
- `value: number`
- `change?: number` (percentage change)
- `icon?: ReactNode`
- `trend?: 'up' | 'down'`

---

## 6. API Integration

### 6.1 Backend Endpoints
**All requests must include `X-API-Key` header**

#### 6.1.1 Transactions
- `GET /api/transactions?year=2024&month=1` - List transactions
- `POST /api/transactions` - Create transaction
- `PUT /api/transactions/{id}` - Update transaction
- `DELETE /api/transactions/{id}` - Delete transaction

#### 6.1.2 Investments
- `GET /api/investments` - List all holdings
- `POST /api/investments` - Add stock purchase

#### 6.1.3 Master Data
- `GET /api/categories` - List categories/subcategories
- `GET /api/accounts` - List accounts
- `GET /api/budgets` - List budget settings

#### 6.1.4 Analytics
- `GET /api/summary?year=2024&month=1` - Income/Expense/Saving summary
- `GET /api/daily-expenses?year=2024&month=1` - Daily expense data for chart
- `GET /api/budget-progress?year=2024&month=1` - Budget vs. actual spending

#### 6.1.5 Market Data (New)
- `GET /api/market-data?symbols=AAPL,GOOGL` - Get current stock prices

### 6.2 Error Handling
**Global error handling strategy:**
- Show toast notifications for API errors
- Retry logic for network failures (3 retries with exponential backoff)
- Graceful degradation (show cached data if available)

### 6.3 Loading States
- Skeleton loaders for tables/charts
- Spinner for button actions
- Optimistic UI updates where possible

---

## 7. Acceptance Criteria

### 7.1 Functional Requirements
- [ ] All 5 pages render correctly with appropriate layouts
- [ ] Quick Action modal works for all 4 transaction types
- [ ] Global Year/Month filter updates Dashboard and Transactions page
- [ ] Flagged transactions show badge and can be approved/edited
- [ ] Transaction edit/delete functionality works
- [ ] Settings page allows CRUD operations on accounts, categories, budgets
- [ ] Market data integration shows real-time stock prices and P/L calculations
- [ ] All charts render with correct data (Recharts)
- [ ] Responsive design works on mobile/tablet/desktop

### 7.2 Non-Functional Requirements
- [ ] Page load time < 2 seconds
- [ ] All API calls include authentication header
- [ ] Error messages are user-friendly
- [ ] Form validation prevents invalid data submission
- [ ] TypeScript strict mode enabled with no type errors

### 7.3 Visual/UX Requirements
- [ ] Design matches modern aesthetic (teal/red palette, premium feel)
- [ ] Smooth animations and transitions
- [ ] Accessible (ARIA labels, keyboard navigation)
- [ ] Consistent spacing and typography across pages

---

## 8. Implementation Phases

### Phase 4.1 - Foundation (Week 1)
- [x] Next.js project setup
- [x] Design system configuration (Tailwind + shadcn/ui)
- [x] Layout components (Sidebar, Header)
- [x] API client setup with authentication

### Phase 4.2 - Core Pages (Week 2)
- [x] Dashboard Overview page
- [x] Transactions page with table
- [x] Quick Action modal (all 4 types)

### Phase 4.3 - Advanced Features (Week 3)
- [ ] Assets & Portfolio page
- [ ] Budget Management page
- [ ] Transaction edit/approve functionality
- [ ] Market data integration

### Phase 4.4 - Settings & Polish (Week 4)
- [ ] Settings page (accounts, categories, budgets management)
- [ ] Filter implementations
- [ ] Responsive design refinements
- [ ] Testing and bug fixes

---

**End of Phase 4 Requirements Document**
