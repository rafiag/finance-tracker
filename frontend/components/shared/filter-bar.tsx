"use client";

import { useEffect, useState } from "react";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { X } from "lucide-react";

interface FilterBarProps {
    showDateFilter?: boolean; // For simplicity, just Year/Month for now
    showAccountFilter?: boolean;
    showCategoryFilter?: boolean;
    showTypeFilter?: boolean;
    onFilterChange: (filters: any) => void;
    accounts?: { name: string }[];
    categories?: string[];
}

export function FilterBar({
    showDateFilter = true,
    showAccountFilter = true,
    showCategoryFilter = true,
    showTypeFilter = true,
    onFilterChange,
    accounts = [],
    categories = []
}: FilterBarProps) {
    const currentYear = new Date().getFullYear();
    const [year, setYear] = useState<string>(currentYear.toString());
    const [month, setMonth] = useState<string>((new Date().getMonth() + 1).toString());
    const [account, setAccount] = useState<string>("all");
    const [category, setCategory] = useState<string>("all");
    const [type, setType] = useState<string>("all");

    // Debounce or effect to trigger change
    useEffect(() => {
        const filters: any = {};
        if (showDateFilter) {
            filters.year = parseInt(year);
            filters.month = parseInt(month);
        }
        if (showAccountFilter && account !== "all") filters.account = account;
        if (showCategoryFilter && category !== "all") filters.category = category;
        if (showTypeFilter && type !== "all") filters.type = type;

        onFilterChange(filters);
    }, [year, month, account, category, type, showDateFilter, showAccountFilter, showCategoryFilter, showTypeFilter, onFilterChange]);

    const resetFilters = () => {
        setYear(currentYear.toString());
        setMonth((new Date().getMonth() + 1).toString());
        setAccount("all");
        setCategory("all");
        setType("all");
    };

    return (
        <div className="flex flex-wrap items-center gap-2 mb-4 p-2 bg-card rounded-lg border">
            {showDateFilter && (
                <>
                    <Select value={year} onValueChange={setYear}>
                        <SelectTrigger className="w-[100px]">
                            <SelectValue placeholder="Year" />
                        </SelectTrigger>
                        <SelectContent>
                            <SelectItem value="2024">2024</SelectItem>
                            <SelectItem value="2025">2025</SelectItem>
                            <SelectItem value="2026">2026</SelectItem>
                        </SelectContent>
                    </Select>

                    <Select value={month} onValueChange={setMonth}>
                        <SelectTrigger className="w-[130px]">
                            <SelectValue placeholder="Month" />
                        </SelectTrigger>
                        <SelectContent>
                            {Array.from({ length: 12 }, (_, i) => i + 1).map((m) => (
                                <SelectItem key={m} value={m.toString()}>
                                    {new Date(0, m - 1).toLocaleString('default', { month: 'long' })}
                                </SelectItem>
                            ))}
                        </SelectContent>
                    </Select>
                </>
            )}

            {showAccountFilter && (
                <Select value={account} onValueChange={setAccount}>
                    <SelectTrigger className="w-[150px]">
                        <SelectValue placeholder="All Accounts" />
                    </SelectTrigger>
                    <SelectContent>
                        <SelectItem value="all">All Accounts</SelectItem>
                        {accounts.map((acc) => (
                            <SelectItem key={acc.name} value={acc.name}>{acc.name}</SelectItem>
                        ))}
                    </SelectContent>
                </Select>
            )}

            {showTypeFilter && (
                <Select value={type} onValueChange={setType}>
                    <SelectTrigger className="w-[130px]">
                        <SelectValue placeholder="All Types" />
                    </SelectTrigger>
                    <SelectContent>
                        <SelectItem value="all">All Types</SelectItem>
                        <SelectItem value="Income">Income</SelectItem>
                        <SelectItem value="Expense">Expense</SelectItem>
                        <SelectItem value="Transfer">Transfer</SelectItem>
                        <SelectItem value="Stock">Stock</SelectItem>
                    </SelectContent>
                </Select>
            )}

            <Button variant="ghost" size="icon" onClick={resetFilters} title="Reset Filters">
                <X className="h-4 w-4" />
            </Button>
        </div>
    );
}
