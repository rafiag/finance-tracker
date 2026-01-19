"use client";

import { useEffect, useState } from "react";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue
} from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { X, Search } from "lucide-react";
import { debounce } from "@/lib/utils";

interface FilterBarProps {
    showDateFilter?: boolean;
    showAccountFilter?: boolean;
    showCategoryFilter?: boolean;
    showTypeFilter?: boolean;
    showStatusFilter?: boolean;
    showSearch?: boolean;
    onFilterChange: (filters: any) => void;
    accounts?: { name: string }[];
    categories?: { name: string; type: string }[];
}

export function FilterBar({
    showDateFilter = true,
    showAccountFilter = true,
    showCategoryFilter = false,
    showTypeFilter = true,
    showStatusFilter = false,
    showSearch = false,
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
    const [status, setStatus] = useState<string>("all");
    const [search, setSearch] = useState<string>("");

    // Debounced search handler
    const debouncedSearch = debounce((value: string) => {
        triggerFilterChange({ search: value });
    }, 300);

    const handleSearchChange = (value: string) => {
        setSearch(value);
        debouncedSearch(value);
    };

    const triggerFilterChange = (extraFilters: any = {}) => {
        const filters: any = { ...extraFilters };

        if (showDateFilter) {
            filters.year = parseInt(year);
            filters.month = parseInt(month);
        }
        if (showAccountFilter && account !== "all") filters.account = account;
        if (showCategoryFilter && category !== "all") filters.category = category;
        if (showTypeFilter && type !== "all") filters.type = type;
        if (showStatusFilter && status !== "all") filters.status = status;
        if (showSearch && search) filters.search = search;

        onFilterChange(filters);
    };

    useEffect(() => {
        triggerFilterChange();
    }, [year, month, account, category, type, status]);

    const resetFilters = () => {
        setYear(currentYear.toString());
        setMonth((new Date().getMonth() + 1).toString());
        setAccount("all");
        setCategory("all");
        setType("all");
        setStatus("all");
        setSearch("");
        onFilterChange({
            year: currentYear,
            month: new Date().getMonth() + 1,
            account: "all",
            category: "all",
            type: "all",
            status: "all",
            search: ""
        });
    };

    // Get unique category names
    const uniqueCategories = Array.from(new Set(categories.map(c => c.name))).sort();

    return (
        <div className="flex flex-wrap items-center gap-2 mb-4 p-3 bg-card rounded-lg border">
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

            {showAccountFilter && accounts.length > 0 && (
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

            {showCategoryFilter && uniqueCategories.length > 0 && (
                <Select value={category} onValueChange={setCategory}>
                    <SelectTrigger className="w-[150px]">
                        <SelectValue placeholder="All Categories" />
                    </SelectTrigger>
                    <SelectContent>
                        <SelectItem value="all">All Categories</SelectItem>
                        {uniqueCategories.map((cat) => (
                            <SelectItem key={cat} value={cat}>{cat}</SelectItem>
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
                        <SelectItem value="Asset">Asset</SelectItem>
                    </SelectContent>
                </Select>
            )}

            {showStatusFilter && (
                <Select value={status} onValueChange={setStatus}>
                    <SelectTrigger className="w-[130px]">
                        <SelectValue placeholder="All Status" />
                    </SelectTrigger>
                    <SelectContent>
                        <SelectItem value="all">All Status</SelectItem>
                        <SelectItem value="Normal">Normal</SelectItem>
                        <SelectItem value="Flagged">Flagged</SelectItem>
                    </SelectContent>
                </Select>
            )}

            {showSearch && (
                <div className="relative flex-1 min-w-[200px]">
                    <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                    <Input
                        placeholder="Search descriptions..."
                        value={search}
                        onChange={(e) => handleSearchChange(e.target.value)}
                        className="pl-8"
                    />
                </div>
            )}

            <Button variant="ghost" size="icon" onClick={resetFilters} title="Reset Filters">
                <X className="h-4 w-4" />
            </Button>
        </div>
    );
}
