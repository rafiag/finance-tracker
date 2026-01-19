'use client';

import { useMemo } from 'react';
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { Account, Investment } from '@/lib/services';
import { formatCompactCurrency, formatCurrency } from '@/lib/utils';

interface NetWorthChartProps {
  accounts: Account[];
  investments: Investment[];
}

export function NetWorthChart({ accounts, investments }: NetWorthChartProps) {
  const netWorth = useMemo(() => {
    const accountsTotal = accounts.reduce((sum, account) => sum + account.balance, 0);
    const investmentsTotal = investments.reduce(
      (sum, inv) => sum + inv.avg_price * inv.shares * (inv.exchange_rate || 1),
      0
    );
    return accountsTotal + investmentsTotal;
  }, [accounts, investments]);

  // Generate mock historical data for the chart
  // In a real implementation, this would come from the backend
  const chartData = useMemo(() => {
    const months = 6;
    const data = [];
    const today = new Date();

    for (let i = months - 1; i >= 0; i--) {
      const date = new Date(today);
      date.setMonth(date.getMonth() - i);

      // Mock data: gradually increase towards current net worth
      const growthFactor = 1 - (i * 0.05);
      const value = Math.round(netWorth * growthFactor);

      data.push({
        month: date.toLocaleDateString('en-US', { month: 'short', year: 'numeric' }),
        value: value,
      });
    }

    return data;
  }, [netWorth]);

  return (
    <div className="space-y-4">
      {/* Net Worth Display */}
      <div className="space-y-1">
        <p className="text-sm text-muted-foreground">Total Net Worth</p>
        <p className="text-4xl font-bold">{formatCurrency(netWorth)}</p>
      </div>

      {/* Chart */}
      <div className="h-[300px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="netWorthGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#14b8a6" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#14b8a6" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
            <XAxis
              dataKey="month"
              className="text-xs"
              tick={{ fill: 'currentColor' }}
            />
            <YAxis
              className="text-xs"
              tick={{ fill: 'currentColor' }}
              tickFormatter={(value) => formatCompactCurrency(value)}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: 'hsl(var(--card))',
                border: '1px solid hsl(var(--border))',
                borderRadius: '8px',
              }}
              formatter={(value: number) => [formatCurrency(value), 'Net Worth']}
            />
            <Area
              type="monotone"
              dataKey="value"
              stroke="#14b8a6"
              strokeWidth={2}
              fill="url(#netWorthGradient)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <p className="text-xs text-muted-foreground">
        * Historical data is approximated. Future updates will include actual historical tracking.
      </p>
    </div>
  );
}
