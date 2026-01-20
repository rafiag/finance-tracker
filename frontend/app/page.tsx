"use client";

import { useEffect, useState } from "react";
import { PiggyBank, CreditCard } from "lucide-react";
import { IncomeCard, SummaryCard, AccountList } from "@/components/dashboard/dashboard-cards";
import { ExpenseChart } from "@/components/dashboard/expense-chart";
import { DashboardSkeleton } from "@/components/skeletons/dashboard-skeleton";
import { fetchSummary, fetchDailyExpenses, fetchAccounts, Summary, Account } from "@/lib/services";

export default function Dashboard() {
  const [summary, setSummary] = useState<Summary | null>(null);
  const [expenses, setExpenses] = useState<any[]>([]);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      try {
        const currentYear = new Date().getFullYear();
        const currentMonth = new Date().getMonth() + 1;

        // Fetch data in parallel
        const [summaryData, expensesData, accountsData] = await Promise.all([
          fetchSummary(currentYear, currentMonth),
          fetchDailyExpenses(currentYear, currentMonth),
          fetchAccounts()
        ]);

        setSummary(summaryData);
        setExpenses(expensesData);
        setAccounts(accountsData);
      } catch (error) {
        console.error("Failed to load dashboard data", error);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  if (loading) {
    return <DashboardSkeleton />;
  }

  if (!summary) {
    // Fallback if data fails completely
    return <div className="p-8">Failed to load dashboard data.</div>;
  }

  return (
    <div className="p-6 space-y-6 animate-in fade-in duration-500">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold tracking-tight">Dashboard</h2>
        <div className="flex items-center space-x-2">
          {/* Add Filter Component Here Later */}
          <span className="text-sm text-muted-foreground">Overview</span>
        </div>
      </div>

      {/* Top Cards Section */}
      <div className="grid gap-4 grid-cols-12">
        {/* Large Income Card */}
        <IncomeCard data={summary.income} />

        {/* Summary Cards */}
        <SummaryCard
          title="Total Expenses"
          amount={summary.expense.total}
          changePercent={summary.expense.change_percent}
          trend={summary.expense.trend}
          type="expense"
          icon={<CreditCard className="h-4 w-4 text-muted-foreground" />}
        />

        <SummaryCard
          title="Total Savings"
          amount={summary.saving.total}
          changePercent={summary.saving.change_percent}
          trend={summary.saving.trend}
          type="savings"
          icon={<PiggyBank className="h-4 w-4 text-muted-foreground" />}
        />
      </div>

      {/* Main Content Section */}
      <div className="grid gap-4 grid-cols-12">
        {/* Expense Chart */}
        <ExpenseChart data={expenses} />

        {/* Account List Widget */}
        <AccountList accounts={accounts} />
      </div>
    </div>
  );
}
