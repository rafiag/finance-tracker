'use client';

import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Budget } from '@/lib/services';
import { formatCurrency, formatPercentage, getBudgetStatus, cn } from '@/lib/utils';
import { TrendingUp, TrendingDown, AlertCircle } from 'lucide-react';

interface BudgetProgressCardProps {
  budget: Budget;
}

export function BudgetProgressCard({ budget }: BudgetProgressCardProps) {
  const status = getBudgetStatus(budget.percentage);
  const remaining = budget.limit - budget.spent;

  return (
    <Card className="overflow-hidden">
      <CardContent className="p-6">
        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            <h3 className="font-semibold text-lg">{budget.category}</h3>
            <p className="text-sm text-muted-foreground">
              Budget: {formatCurrency(budget.limit)}
            </p>
          </div>
          <Badge
            variant={status.variant}
            className={cn(
              "ml-2",
              budget.percentage >= 100 && "bg-red-500 hover:bg-red-600",
              budget.percentage >= 80 && budget.percentage < 100 && "bg-yellow-500 hover:bg-yellow-600 text-white",
              budget.percentage < 80 && "bg-green-500 hover:bg-green-600"
            )}
          >
            {status.label}
          </Badge>
        </div>

        {/* Progress Bar */}
        <div className="space-y-2 mb-4">
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Spent</span>
            <span className="font-medium">{formatCurrency(budget.spent)}</span>
          </div>

          <div className="w-full bg-muted rounded-full h-3 overflow-hidden">
            <div
              className={cn(
                "h-full rounded-full transition-all duration-300",
                budget.percentage >= 100 && "bg-red-500",
                budget.percentage >= 80 && budget.percentage < 100 && "bg-yellow-500",
                budget.percentage < 80 && "bg-green-500"
              )}
              style={{ width: `${Math.min(budget.percentage, 100)}%` }}
            />
          </div>

          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">
              {formatPercentage(budget.percentage)} used
            </span>
            <span className={cn(
              "font-medium",
              remaining >= 0 ? "text-muted-foreground" : "text-red-600 dark:text-red-400"
            )}>
              {remaining >= 0 ? formatCurrency(remaining) : formatCurrency(Math.abs(remaining))} {remaining >= 0 ? 'left' : 'over'}
            </span>
          </div>
        </div>

        {/* Warning Message */}
        {budget.percentage >= 80 && (
          <div className={cn(
            "flex items-center gap-2 p-3 rounded-lg text-sm",
            budget.percentage >= 100 ? "bg-red-50 dark:bg-red-950 text-red-700 dark:text-red-300" :
              "bg-yellow-50 dark:bg-yellow-950 text-yellow-700 dark:text-yellow-300"
          )}>
            <AlertCircle className="h-4 w-4 flex-shrink-0" />
            <span>
              {budget.percentage >= 100
                ? `Over budget by ${formatCurrency(Math.abs(remaining))}`
                : `Approaching budget limit (${formatPercentage(100 - budget.percentage)} remaining)`
              }
            </span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
