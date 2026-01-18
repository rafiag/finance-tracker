import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ArrowDownIcon, ArrowUpIcon, Wallet, PiggyBank, CreditCard } from "lucide-react";
import { cn, formatCurrency } from "@/lib/utils";
import { DashboardSummary, Account } from "@/lib/services";

interface IncomeCardProps {
    data: DashboardSummary['income'];
}

export function IncomeCard({ data }: IncomeCardProps) {
    return (
        <Card className="col-span-12 lg:col-span-4 bg-gradient-to-br from-income-500/10 to-income-600/5 dark:from-income-900/20 dark:to-income-900/10 border-income-200 dark:border-income-900">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-income-600 dark:text-income-400">Total Income</CardTitle>
                <Wallet className="h-4 w-4 text-income-600 dark:text-income-400" />
            </CardHeader>
            <CardContent>
                <div className="text-2xl font-bold text-income-700 dark:text-income-300">
                    {formatCurrency(data.total)}
                </div>
                <p className="text-xs text-muted-foreground pt-1">
                    {data.change_percent >= 0 ? (
                        <span className="text-income-600 flex items-center gap-1">
                            <ArrowUpIcon className="h-3 w-3" />
                            {data.change_percent}%
                        </span>
                    ) : (
                        <span className="text-expense-600 flex items-center gap-1">
                            <ArrowDownIcon className="h-3 w-3" />
                            {Math.abs(data.change_percent)}%
                        </span>
                    )}
                    <span className="ml-1">from last month</span>
                </p>
            </CardContent>
        </Card>
    );
}

interface SummaryCardProps {
    title: string;
    amount: number;
    changePercent: number;
    trend: 'up' | 'down';
    icon: React.ReactNode;
    type: 'savings' | 'expense';
}

export function SummaryCard({ title, amount, changePercent, trend, icon, type }: SummaryCardProps) {
    const isPositive = changePercent >= 0;
    const trendColor = type === 'savings'
        ? (isPositive ? 'text-income-600' : 'text-expense-600')
        : (isPositive ? 'text-expense-600' : 'text-income-600'); // For expenses, increase is usually "bad" (red), decrease is "good" (green)

    // Logic for expenses: "Up" means more spending (Red often), but techincally 'trend' prop usually just means direction.
    // Let's stick to: Increase in savings = Green. Increase in expenses = Red.
    // changePercent is just the number. 

    const displayColor = type === 'expense' ? 'text-expense-600 dark:text-expense-400' : 'text-income-600 dark:text-income-400';

    return (
        <Card className="col-span-12 sm:col-span-6 lg:col-span-4">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">{title}</CardTitle>
                {icon}
            </CardHeader>
            <CardContent>
                <div className="text-2xl font-bold">{formatCurrency(amount)}</div>
                <div className="flex items-center text-xs text-muted-foreground pt-1">
                    <span className={cn("flex items-center gap-1", trendColor)}>
                        {changePercent >= 0 ? <ArrowUpIcon className="h-3 w-3" /> : <ArrowDownIcon className="h-3 w-3" />}
                        {Math.abs(changePercent)}%
                    </span>
                    <span className="ml-1">from last month</span>
                </div>
            </CardContent>
        </Card>
    );
}

interface AccountListProps {
    accounts: Account[];
}

export function AccountList({ accounts }: AccountListProps) {
    return (
        <Card className="col-span-12 lg:col-span-4 max-h-[400px] overflow-auto">
            <CardHeader>
                <CardTitle>Accounts</CardTitle>
            </CardHeader>
            <CardContent className="grid gap-4">
                {accounts.map((account) => (
                    <div key={account.name} className="flex items-center justify-between p-2 rounded-lg border bg-card hover:bg-accent/50 transition-colors">
                        <div className="flex items-center gap-3">
                            <div className="bg-primary/10 p-2 rounded-full">
                                <CreditCard className="h-4 w-4 text-primary" />
                            </div>
                            <div>
                                <p className="text-sm font-medium leading-none">{account.name}</p>
                                <p className="text-xs text-muted-foreground">{account.type}</p>
                            </div>
                        </div>
                        <div className="text-sm font-bold">
                            {formatCurrency(account.balance)}
                        </div>
                    </div>
                ))}
                {accounts.length === 0 && (
                    <div className="text-center text-sm text-muted-foreground py-4">No accounts found.</div>
                )}
            </CardContent>
        </Card>
    );
}
