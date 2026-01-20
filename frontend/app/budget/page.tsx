'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Settings } from 'lucide-react';
import { BudgetProgressCard } from '@/components/budget/budget-progress-card';
import { HistoricalPerformance } from '@/components/budget/historical-performance';
import { fetchBudgetProgress, Budget } from '@/lib/services';
import { getCurrentYearMonth } from '@/lib/utils';
import { useRouter } from 'next/navigation';

export default function BudgetPage() {
  const [budgets, setBudgets] = useState<Budget[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    loadBudgets();
  }, []);

  async function loadBudgets() {
    try {
      setIsLoading(true);
      const { year, month } = getCurrentYearMonth();
      const data = await fetchBudgetProgress(year, month);
      setBudgets(data);
    } catch (error) {
      console.error('Error loading budgets:', error);
    } finally {
      setIsLoading(false);
    }
  }

  const handleEditBudgets = () => {
    router.push('/settings');
  };

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Budget Management</h1>
        <Button onClick={handleEditBudgets} variant="outline" className="gap-2">
          <Settings className="h-4 w-4" />
          Edit Budgets
        </Button>
      </div>

      {/* Current Month Budget Overview */}
      <Card>
        <CardHeader>
          <CardTitle>Current Month Budget Progress</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="p-8 text-center">Loading budget data...</div>
          ) : budgets.length === 0 ? (
            <div className="p-8 text-center border rounded-lg bg-muted/20">
              <p className="mb-4">No budgets configured yet.</p>
              <Button onClick={handleEditBudgets}>Set Up Budgets</Button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {budgets.map((budget) => (
                <BudgetProgressCard key={budget.category} budget={budget} />
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Historical Budget Performance */}
      {!isLoading && budgets.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Category Performance Over Time</CardTitle>
          </CardHeader>
          <CardContent>
            <HistoricalPerformance budgets={budgets} />
          </CardContent>
        </Card>
      )}
    </div>
  );
}
