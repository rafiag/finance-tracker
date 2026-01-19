"use client";

import { useEffect, useState, useCallback } from "react";
import { FilterBar } from "@/components/shared/filter-bar";
import { TransactionsTable } from "@/components/transactions/transactions-table";
import { fetchTransactions, fetchAccounts, Transaction, Account } from "@/lib/services";

export default function TransactionsPage() {
    const [transactions, setTransactions] = useState<Transaction[]>([]);
    const [accounts, setAccounts] = useState<Account[]>([]);
    const [loading, setLoading] = useState(true);
    const [filters, setFilters] = useState<Record<string, unknown>>({
        year: new Date().getFullYear(),
        month: new Date().getMonth() + 1,
        account: 'all',
        category: 'all',
        type: 'all'
    });

    useEffect(() => {
        // Fetch accounts for filter dropdown
        const loadAccounts = async () => {
            const data = await fetchAccounts();
            setAccounts(data);
        };
        loadAccounts();
    }, []);

    const loadTransactions = useCallback(async () => {
        setLoading(true);
        try {
            const year = filters.year as number;
            const month = filters.month as number;

            // Fetch all transactions for the selected period
            const data = await fetchTransactions(year, month);

            // Apply client-side filters
            let filtered = data;

            if (filters.account !== 'all') {
                filtered = filtered.filter(t => t.account === filters.account);
            }

            if (filters.category !== 'all') {
                filtered = filtered.filter(t => t.category === filters.category);
            }

            if (filters.type !== 'all') {
                filtered = filtered.filter(t => t.type === filters.type);
            }

            setTransactions(filtered);
        } catch (error) {
            console.error("Failed to load transactions", error);
        } finally {
            setLoading(false);
        }
    }, [filters]);

    useEffect(() => {
        loadTransactions();
    }, [loadTransactions]);

    const handleFilterChange = useCallback((newFilters: Record<string, unknown>) => {
        setFilters((prev) => {
            // Only update if filters actually changed to avoid unnecessary re-renders
            const updated = { ...prev, ...newFilters };
            if (JSON.stringify(updated) === JSON.stringify(prev)) return prev;
            return updated;
        });
    }, []);

    return (
        <div className="p-6 space-y-6">
            <div className="flex items-center justify-between">
                <h2 className="text-3xl font-bold tracking-tight">Transactions</h2>
            </div>

            <FilterBar
                onFilterChange={handleFilterChange}
                accounts={accounts}
                showCategoryFilter={false} // Category filter needs category list which we haven't fetched yet. simplification for now.
            />

            <div className="space-y-4">
                <TransactionsTable
                    transactions={transactions}
                    isLoading={loading}
                    onRefresh={loadTransactions}
                />
            </div>
        </div>
    );
}
