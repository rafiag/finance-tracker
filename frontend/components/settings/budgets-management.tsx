'use client';

import { useEffect, useState } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { fetchCategories, updateBudgets, fetchBudgets, Category } from '@/lib/services';
import { formatCurrency } from '@/lib/utils';
import { Loader2, Save } from 'lucide-react';
import { toast } from 'sonner';

interface BudgetRow {
  category: string;
  monthly_budget: number;
  effective_from: string;
}

export function BudgetsManagement() {
  const [categories, setCategories] = useState<Category[]>([]);
  const [budgets, setBudgets] = useState<Map<string, BudgetRow>>(new Map());
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    try {
      setIsLoading(true);
      const [categoriesData, budgetsData] = await Promise.all([
        fetchCategories(),
        fetchBudgets(),
      ]);

      // Filter only expense categories
      const expenseCategories = categoriesData.filter((cat) => cat.type === 'Expense');
      setCategories(expenseCategories);

      // Map existing budgets
      const budgetMap = new Map<string, BudgetRow>();
      budgetsData.forEach((budget) => {
        budgetMap.set(budget.category, {
          category: budget.category,
          monthly_budget: budget.limit,
          effective_from: budget.effective_from || '',
        });
      });

      // Add categories without budgets
      expenseCategories.forEach((cat) => {
        if (!budgetMap.has(cat.name)) {
          budgetMap.set(cat.name, {
            category: cat.name,
            monthly_budget: 0,
            effective_from: '',
          });
        }
      });

      setBudgets(budgetMap);
    } catch (error) {
      console.error('Error loading data:', error);
      toast.error('Failed to load budgets');
    } finally {
      setIsLoading(false);
    }
  }

  const handleBudgetChange = (category: string, value: number) => {
    const newBudgets = new Map(budgets);
    const budget = newBudgets.get(category)!;
    budget.monthly_budget = value;
    newBudgets.set(category, budget);
    setBudgets(newBudgets);
  };

  const handleSaveAll = async () => {
    try {
      setIsSaving(true);

      // Calculate next month's date for effective_from
      const nextMonth = new Date();
      nextMonth.setMonth(nextMonth.getMonth() + 1);
      nextMonth.setDate(1);
      const defaultEffectiveFrom = nextMonth.toISOString().split('T')[0];

      // Prepare budgets array (only non-zero budgets)
      const budgetsArray = Array.from(budgets.values())
        .filter((b) => b.monthly_budget > 0)
        .map((b) => ({
          category: b.category,
          monthly_budget: b.monthly_budget,
          effective_from: b.effective_from || defaultEffectiveFrom,
        }));

      if (budgetsArray.length === 0) {
        toast.info('No budgets to save. Set budget amounts greater than 0.');
        return;
      }

      await updateBudgets(budgetsArray);
      toast.success(`Successfully updated ${budgetsArray.length} budget(s). Changes will take effect next month.`, {
        duration: 5000,
      });
      loadData(); // Reload to get updated data
    } catch (error) {
      console.error('Error saving budgets:', error);
      toast.error('Failed to save budgets');
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return <div className="p-8 text-center">Loading budgets...</div>;
  }

  // Get unique categories (no duplicates for categories with multiple subcategories)
  const uniqueCategories = Array.from(
    new Set(categories.map((cat) => cat.name))
  ).sort();

  return (
    <div className="space-y-4">
      <div className="rounded-lg bg-blue-50 dark:bg-blue-950 p-4 border border-blue-200 dark:border-blue-800">
        <p className="text-sm text-blue-900 dark:text-blue-100">
          <strong>Note:</strong> Budget changes will take effect starting next month. Set your monthly spending limits
          for each expense category below.
        </p>
      </div>

      <div className="rounded-md border bg-card">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Category</TableHead>
              <TableHead className="w-[300px]">Monthly Budget (IDR)</TableHead>
              <TableHead className="text-right">Status</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {uniqueCategories.length === 0 ? (
              <TableRow>
                <TableCell colSpan={3} className="text-center text-muted-foreground">
                  No expense categories found. Create categories in the Categories tab first.
                </TableCell>
              </TableRow>
            ) : (
              uniqueCategories.map((category) => {
                const budget = budgets.get(category);
                const hasValidBudget = budget && budget.monthly_budget > 0;

                return (
                  <TableRow key={category}>
                    <TableCell className="font-medium">{category}</TableCell>
                    <TableCell>
                      <Input
                        type="number"
                        value={budget?.monthly_budget || 0}
                        onChange={(e) =>
                          handleBudgetChange(category, parseFloat(e.target.value) || 0)
                        }
                        min="0"
                        step="10000"
                        placeholder="Enter budget amount"
                      />
                    </TableCell>
                    <TableCell className="text-right">
                      {hasValidBudget ? (
                        <span className="text-sm text-green-600 dark:text-green-400">
                          {formatCurrency(budget.monthly_budget)} / month
                        </span>
                      ) : (
                        <span className="text-sm text-muted-foreground">No budget set</span>
                      )}
                    </TableCell>
                  </TableRow>
                );
              })
            )}
          </TableBody>
        </Table>
      </div>

      {uniqueCategories.length > 0 && (
        <div className="flex justify-end">
          <Button onClick={handleSaveAll} disabled={isSaving} className="gap-2">
            {isSaving ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Saving...
              </>
            ) : (
              <>
                <Save className="h-4 w-4" />
                Save All Budgets
              </>
            )}
          </Button>
        </div>
      )}
    </div>
  );
}
