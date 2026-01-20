'use client';

import { useMemo } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Bar, BarChart, ResponsiveContainer, XAxis, YAxis, Tooltip, Cell } from 'recharts';
import { Budget } from '@/lib/services';
import { formatCurrency, formatCompactCurrency, getCurrentYearMonth } from '@/lib/utils';

interface HistoricalPerformanceProps {
  budgets: Budget[];
}

export function HistoricalPerformance({ budgets }: HistoricalPerformanceProps) {
  // Generate mock historical data for demonstration
  // In a real implementation, this would come from the backend
  const historicalData = useMemo(() => {
    const { month: currentMonth } = getCurrentYearMonth();
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

    return budgets.map(budget => {
      // Generate 3 months of mock data
      const last3Months = [];
      for (let i = 2; i >= 0; i--) {
        const monthIndex = (currentMonth - 1 - i + 12) % 12;
        // Mock spending: vary around current spending ±20%
        const variation = 0.8 + (Math.random() * 0.4);
        const amount = Math.round(budget.spent * variation);

        last3Months.push({
          month: months[monthIndex],
          amount: amount,
          percentage: budget.limit > 0 ? (amount / budget.limit * 100) : 0,
        });
      }

      // Calculate average
      const avgSpending = Math.round(
        last3Months.reduce((sum, m) => sum + m.amount, 0) / last3Months.length
      );

      return {
        category: budget.category,
        months: last3Months,
        average: avgSpending,
        budget: budget.limit,
      };
    });
  }, [budgets]);

  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">
        View your spending patterns across categories for the last 3 months
      </p>

      <div className="rounded-md border bg-card">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-[200px]">Category</TableHead>
              <TableHead className="w-[300px]">Last 3 Months</TableHead>
              <TableHead className="text-right">Average</TableHead>
              <TableHead className="text-right">Budget Limit</TableHead>
              <TableHead className="text-right">Avg vs Budget</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {historicalData.map((item) => {
              const avgPercentage = item.budget > 0 ? (item.average / item.budget * 100) : 0;
              const isOverBudget = avgPercentage >= 100;

              return (
                <TableRow key={item.category}>
                  <TableCell className="font-medium">{item.category}</TableCell>
                  <TableCell>
                    <div className="h-12 w-full">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={item.months}>
                          <XAxis
                            dataKey="month"
                            tick={{ fontSize: 10 }}
                            axisLine={false}
                            tickLine={false}
                          />
                          <YAxis hide />
                          <Tooltip
                            contentStyle={{
                              backgroundColor: 'hsl(var(--card))',
                              border: '1px solid hsl(var(--border))',
                              borderRadius: '8px',
                              fontSize: '12px',
                            }}
                            formatter={(value: number) => formatCurrency(value)}
                          />
                          <Bar dataKey="amount" radius={[4, 4, 0, 0]}>
                            {item.months.map((entry, index) => (
                              <Cell
                                key={`cell-${index}`}
                                fill={
                                  entry.percentage >= 100
                                    ? '#ef4444'
                                    : entry.percentage >= 80
                                    ? '#eab308'
                                    : '#22c55e'
                                }
                              />
                            ))}
                          </Bar>
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </TableCell>
                  <TableCell className="text-right font-medium">
                    {formatCurrency(item.average)}
                  </TableCell>
                  <TableCell className="text-right">
                    {formatCurrency(item.budget)}
                  </TableCell>
                  <TableCell className={`text-right font-medium ${
                    isOverBudget ? 'text-red-600 dark:text-red-400' : 'text-green-600 dark:text-green-400'
                  }`}>
                    {isOverBudget ? 'Over' : 'Under'} ({avgPercentage.toFixed(0)}%)
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </div>

      <p className="text-xs text-muted-foreground">
        * Historical data is approximated for demonstration. Future updates will include actual historical tracking.
      </p>
    </div>
  );
}
