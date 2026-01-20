/**
 * API Service Layer
 * Handles all communication with the backend API
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const API_KEY = process.env.NEXT_PUBLIC_API_KEY || '';

// Types
export interface Transaction {
  id: string;
  date: string;
  account: string;
  category: string;
  subcategory?: string;
  description: string;
  amount: number;
  type: 'Income' | 'Expense' | 'Transfer-In' | 'Transfer-Out' | 'Asset';
  status: 'Normal' | 'Flagged';
}

export interface Account {
  name: string;
  type: 'Bank' | 'Cash' | 'E-wallet' | 'Investment';
  balance: number;
  currency: string;
}

export interface Category {
  name: string;
  type: 'Income' | 'Expense';
  subcategories: string[];
}

export interface Budget {
  category: string;
  limit: number;
  spent: number;
  percentage: number;
  effective_from?: string;
}

export interface Investment {
  id: string;
  symbol: string;
  shares: number;
  avg_price: number;
  purchase_date: string;
  account: string;
  currency: string;
  exchange_rate?: number;
}

export interface MarketData {
  symbol: string;
  current_price: number;
  change_percent: number;
  currency: string;
}

export interface Summary {
  income: number;
  expense: number;
  saving: number;
  income_change?: number;
  expense_change?: number;
  saving_change?: number;
}

export interface DailyExpense {
  date: string;
  amount: number;
}

export interface AccountBalance {
  account: string;
  type: string;
  balance: number;
  income_month: number;
  expense_month: number;
}

// Helper function to make API calls with authentication
async function fetchAPI(endpoint: string, options: RequestInit = {}) {
  const url = `${API_URL}${endpoint}`;
  const headers = {
    'Content-Type': 'application/json',
    'X-API-Key': API_KEY,
    ...options.headers,
  };

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `API Error: ${response.status}`);
  }

  return response.json();
}

// Transactions API
export async function fetchTransactions(year?: number, month?: number): Promise<Transaction[]> {
  const params = new URLSearchParams();
  if (year) params.append('year', year.toString());
  if (month) params.append('month', month.toString());

  const query = params.toString();
  const data = await fetchAPI(`/api/transactions${query ? `?${query}` : ''}`);
  return data.transactions || [];
}

export async function createTransaction(transaction: Omit<Transaction, 'id'>): Promise<{ id: string }> {
  return fetchAPI('/api/transactions', {
    method: 'POST',
    body: JSON.stringify(transaction),
  });
}

export async function updateTransaction(id: string, transaction: Partial<Transaction>): Promise<void> {
  await fetchAPI(`/api/transactions/${id}`, {
    method: 'PUT',
    body: JSON.stringify(transaction),
  });
}

export async function deleteTransaction(id: string): Promise<void> {
  await fetchAPI(`/api/transactions/${id}`, {
    method: 'DELETE',
  });
}

// Investments API
export async function fetchInvestments(): Promise<Investment[]> {
  const data = await fetchAPI('/api/investments');
  return data.investments || [];
}

export async function createInvestment(investment: {
  symbol: string;
  shares: number;
  price: number;
  amount: number;
  account?: string;
  source_account?: string;
  date?: string;
  currency?: string;
}): Promise<void> {
  await fetchAPI('/api/investments', {
    method: 'POST',
    body: JSON.stringify(investment),
  });
}

// Transfer API
export async function createTransfer(transfer: {
  from_account: string;
  to_account: string;
  amount: number;
  date: string;
  note?: string;
}): Promise<void> {
  await fetchAPI('/api/transfers', {
    method: 'POST',
    body: JSON.stringify(transfer),
  });
}

// Master Data APIs
export async function fetchAccounts(): Promise<Account[]> {
  const data = await fetchAPI('/api/accounts');
  return data.accounts || [];
}

export async function fetchCategories(): Promise<Category[]> {
  const data = await fetchAPI('/api/categories');
  return data.categories || [];
}

export async function fetchBudgets(year?: number, month?: number): Promise<Budget[]> {
  const params = new URLSearchParams();
  if (year) params.append('year', year.toString());
  if (month) params.append('month', month.toString());

  const query = params.toString();
  const data = await fetchAPI(`/api/budgets${query ? `?${query}` : ''}`);
  return data.budgets || [];
}

// Analytics APIs
export async function fetchSummary(year: number, month: number): Promise<Summary> {
  const data = await fetchAPI(`/api/summary?year=${year}&month=${month}`);
  return data.summary || { income: 0, expense: 0, saving: 0 };
}

export async function fetchDailyExpenses(year: number, month: number): Promise<DailyExpense[]> {
  const data = await fetchAPI(`/api/daily-expenses?year=${year}&month=${month}`);
  return data.daily_expenses || [];
}

export async function fetchBudgetProgress(year: number, month: number): Promise<Budget[]> {
  const data = await fetchAPI(`/api/budget-progress?year=${year}&month=${month}`);
  return data.budget_progress || [];
}

export async function fetchAccountBalances(year?: number, month?: number): Promise<AccountBalance[]> {
  const params = new URLSearchParams();
  if (year) params.append('year', year.toString());
  if (month) params.append('month', month.toString());

  const query = params.toString();
  const data = await fetchAPI(`/api/account-balances${query ? `?${query}` : ''}`);
  return data.account_balances || [];
}

// Market Data API
export async function fetchMarketData(symbols: string[]): Promise<Record<string, MarketData>> {
  if (symbols.length === 0) return {};

  const symbolsParam = symbols.join(',');
  const data = await fetchAPI(`/api/market-data?symbols=${symbolsParam}`);
  return data.market_data || {};
}

// Settings - Accounts API
export async function createAccount(account: { name: string; type: string; currency: string }): Promise<void> {
  await fetchAPI('/api/accounts', {
    method: 'POST',
    body: JSON.stringify(account),
  });
}

export async function updateAccount(
  accountName: string,
  updates: { new_name?: string; type?: string; balance?: number }
): Promise<{ balance_adjusted: boolean; adjustment_amount: number | null }> {
  const data = await fetchAPI(`/api/accounts/${encodeURIComponent(accountName)}`, {
    method: 'PUT',
    body: JSON.stringify(updates),
  });
  return data;
}

export async function deleteAccount(accountName: string): Promise<void> {
  await fetchAPI(`/api/accounts/${encodeURIComponent(accountName)}`, {
    method: 'DELETE',
  });
}

// Settings - Categories API
export async function createCategory(category: {
  category: string;
  type: string;
  subcategory?: string;
}): Promise<void> {
  await fetchAPI('/api/categories', {
    method: 'POST',
    body: JSON.stringify(category),
  });
}

export async function updateCategory(
  categoryName: string,
  subcategoryName: string,
  updates: { new_category?: string; new_subcategory?: string }
): Promise<void> {
  await fetchAPI(
    `/api/categories/${encodeURIComponent(categoryName)}?subcategory_name=${encodeURIComponent(subcategoryName)}`,
    {
      method: 'PUT',
      body: JSON.stringify(updates),
    }
  );
}

export async function deleteCategory(categoryName: string, subcategoryName: string = ''): Promise<void> {
  await fetchAPI(
    `/api/categories/${encodeURIComponent(categoryName)}?subcategory_name=${encodeURIComponent(subcategoryName)}`,
    {
      method: 'DELETE',
    }
  );
}

// Settings - Budgets API
export async function updateBudgets(
  budgets: Array<{ category: string; monthly_budget: number; effective_from?: string }>
): Promise<void> {
  await fetchAPI('/api/budgets', {
    method: 'PUT',
    body: JSON.stringify(budgets),
  });
}
