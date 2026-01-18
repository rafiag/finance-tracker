"use client";

import { useMemo } from "react";
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatCurrency } from "@/lib/utils";

interface ExpenseChartProps {
    data: { date: string; amount: number }[];
}

export function ExpenseChart({ data }: ExpenseChartProps) {
    // Transform data for charts if necessary, or ensure backend sends correct format
    // Expecting data to be sorted by date
    const chartData = useMemo(() => {
        return data.map(item => ({
            day: new Date(item.date).getDate(), // or format as needed
            amount: item.amount,
            fullDate: item.date
        }));
    }, [data]);

    return (
        <Card className="col-span-12 lg:col-span-8">
            <CardHeader>
                <CardTitle>Expense Activity</CardTitle>
            </CardHeader>
            <CardContent className="pl-0">
                <div className="h-[300px] w-full">
                    <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                            <defs>
                                <linearGradient id="colorExpense" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="var(--color-expense-500)" stopOpacity={0.3} />
                                    <stop offset="95%" stopColor="var(--color-expense-500)" stopOpacity={0} />
                                </linearGradient>
                            </defs>
                            <XAxis
                                dataKey="day"
                                stroke="#888888"
                                fontSize={12}
                                tickLine={false}
                                axisLine={false}
                            />
                            <YAxis
                                stroke="#888888"
                                fontSize={12}
                                tickLine={false}
                                axisLine={false}
                                tickFormatter={(value) => formatCurrency(value)}
                            />
                            <Tooltip
                                contentStyle={{ backgroundColor: 'var(--background)', borderRadius: '8px', border: '1px solid var(--border)' }}
                                itemStyle={{ color: 'var(--foreground)' }}
                                formatter={(value: number | string | any) => [formatCurrency(Number(value) || 0), 'Expense']}
                                labelFormatter={(label) => `Day ${label}`}
                            />
                            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border)" />
                            <Area
                                type="monotone"
                                dataKey="amount"
                                stroke="var(--color-expense-500)"
                                fillOpacity={1}
                                fill="url(#colorExpense)"
                                strokeWidth={2}
                            />
                        </AreaChart>
                    </ResponsiveContainer>
                </div>
            </CardContent>
        </Card>
    );
}
