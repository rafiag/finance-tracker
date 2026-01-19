import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

/**
 * Utility function to merge Tailwind CSS classes
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * Format number as Indonesian Rupiah currency
 */
export function formatCurrency(amount: number, currency: string = 'IDR'): string {
  if (currency === 'USD') {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(amount);
  }

  // IDR formatting
  return new Intl.NumberFormat('id-ID', {
    style: 'currency',
    currency: 'IDR',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount);
}

/**
 * Format number as compact currency (e.g., 1.5M, 20K)
 */
export function formatCompactCurrency(amount: number): string {
  if (amount >= 1_000_000_000) {
    return `Rp ${(amount / 1_000_000_000).toFixed(1)}B`;
  }
  if (amount >= 1_000_000) {
    return `Rp ${(amount / 1_000_000).toFixed(1)}M`;
  }
  if (amount >= 1_000) {
    return `Rp ${(amount / 1_000).toFixed(0)}K`;
  }
  return formatCurrency(amount);
}

/**
 * Format date as readable string
 */
export function formatDate(date: string | Date): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  return new Intl.DateTimeFormat('id-ID', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  }).format(d);
}

/**
 * Format date as YYYY-MM-DD for inputs
 */
export function formatDateForInput(date: string | Date): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  return d.toISOString().split('T')[0];
}

/**
 * Calculate percentage
 */
export function calculatePercentage(value: number, total: number): number {
  if (total === 0) return 0;
  return (value / total) * 100;
}

/**
 * Format percentage
 */
export function formatPercentage(value: number, decimals: number = 1): string {
  return `${value.toFixed(decimals)}%`;
}

/**
 * Get color class based on transaction type
 */
export function getTransactionTypeColor(type: string): string {
  switch (type) {
    case 'Income':
      return 'text-income-600 dark:text-income-400';
    case 'Expense':
      return 'text-expense-600 dark:text-expense-400';
    case 'Transfer-In':
    case 'Transfer-Out':
      return 'text-blue-600 dark:text-blue-400';
    case 'Asset':
      return 'text-purple-600 dark:text-purple-400';
    default:
      return 'text-foreground';
  }
}

/**
 * Get budget status badge variant
 */
export function getBudgetStatus(percentage: number): {
  label: string;
  variant: 'default' | 'secondary' | 'destructive' | 'outline';
  color: string;
} {
  if (percentage >= 100) {
    return { label: 'Over Budget', variant: 'destructive', color: 'bg-red-500' };
  }
  if (percentage >= 80) {
    return { label: 'Warning', variant: 'outline', color: 'bg-yellow-500' };
  }
  return { label: 'Safe', variant: 'default', color: 'bg-green-500' };
}

/**
 * Get profit/loss color class
 */
export function getProfitLossColor(value: number): string {
  if (value > 0) return 'text-green-600 dark:text-green-400';
  if (value < 0) return 'text-red-600 dark:text-red-400';
  return 'text-muted-foreground';
}

/**
 * Calculate profit/loss
 */
export function calculateProfitLoss(currentPrice: number, avgPrice: number, shares: number): {
  amount: number;
  percentage: number;
} {
  const totalCost = avgPrice * shares;
  const currentValue = currentPrice * shares;
  const profitLoss = currentValue - totalCost;
  const percentage = totalCost > 0 ? (profitLoss / totalCost) * 100 : 0;

  return {
    amount: profitLoss,
    percentage,
  };
}

/**
 * Debounce function for search/filter inputs
 */
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout;
  return (...args: Parameters<T>) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
}

/**
 * Get current year and month
 */
export function getCurrentYearMonth(): { year: number; month: number } {
  const now = new Date();
  return {
    year: now.getFullYear(),
    month: now.getMonth() + 1, // JavaScript months are 0-indexed
  };
}

/**
 * Get month name
 */
export function getMonthName(month: number): string {
  const months = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
  ];
  return months[month - 1] || '';
}

/**
 * Generate array of years for dropdown
 */
export function getYearOptions(startYear: number = 2020): number[] {
  const currentYear = new Date().getFullYear();
  const years: number[] = [];
  for (let year = currentYear; year >= startYear; year--) {
    years.push(year);
  }
  return years;
}

/**
 * Generate array of months for dropdown
 */
export function getMonthOptions(): Array<{ value: number; label: string }> {
  return [
    { value: 1, label: 'January' },
    { value: 2, label: 'February' },
    { value: 3, label: 'March' },
    { value: 4, label: 'April' },
    { value: 5, label: 'May' },
    { value: 6, label: 'June' },
    { value: 7, label: 'July' },
    { value: 8, label: 'August' },
    { value: 9, label: 'September' },
    { value: 10, label: 'October' },
    { value: 11, label: 'November' },
    { value: 12, label: 'December' },
  ];
}
