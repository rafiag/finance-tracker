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

    useEffect(() => {
        const loadTransactions = async () => {
            setLoading(true);
            try {
                // Prepare params
                const params: Record<string, unknown> = { ...filters };
                if (params.account === 'all') delete params.account;
                if (params.category === 'all') delete params.category;
                if (params.type === 'all') delete params.type;

                const data = await fetchTransactions(params);
                setTransactions(data);
            } catch (error) {
                console.error("Failed to load transactions", error);
            } finally {
                setLoading(false);
            }
        };

        loadTransactions();
    }, [filters]);

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
                <TransactionsTable transactions={transactions} isLoading={loading} />
            </div>
        </div>
    );
}
