'use client';

import { useEffect, useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Transaction, updateTransaction, fetchAccounts, fetchCategories } from '@/lib/services';
import { formatDateForInput } from '@/lib/utils';
import { Loader2 } from 'lucide-react';

interface EditTransactionModalProps {
  transaction: Transaction | null;
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export function EditTransactionModal({
  transaction,
  isOpen,
  onClose,
  onSuccess,
}: EditTransactionModalProps) {
  const [formData, setFormData] = useState<Partial<Transaction>>({});
  const [accounts, setAccounts] = useState<string[]>([]);
  const [categories, setCategories] = useState<{ name: string; subcategories: string[] }[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    if (isOpen) {
      loadMasterData();
      if (transaction) {
        setFormData({
          date: transaction.date,
          account: transaction.account,
          category: transaction.category,
          subcategory: transaction.subcategory,
          description: transaction.description,
          amount: transaction.amount,
          type: transaction.type,
          status: transaction.status,
        });
      }
    }
  }, [isOpen, transaction]);

  async function loadMasterData() {
    try {
      setIsLoading(true);
      const [accountsData, categoriesData] = await Promise.all([
        fetchAccounts(),
        fetchCategories(),
      ]);

      setAccounts(accountsData.map(a => a.name));
      setCategories(categoriesData);
    } catch (error) {
      console.error('Error loading master data:', error);
    } finally {
      setIsLoading(false);
    }
  }

  const selectedCategory = categories.find(c => c.name === formData.category);
  const subcategories = selectedCategory?.subcategories || [];

  const handleSave = async () => {
    if (!transaction) return;

    try {
      setIsSaving(true);

      // Validate required fields
      if (!formData.date || !formData.account || !formData.category || !formData.amount) {
        alert('Please fill in all required fields');
        return;
      }

      await updateTransaction(transaction.id, formData);
      onSuccess();
      onClose();
    } catch (error) {
      console.error('Error updating transaction:', error);
      alert('Failed to update transaction. Please try again.');
    } finally {
      setIsSaving(false);
    }
  };

  const handleApprove = async () => {
    if (!transaction) return;

    try {
      setIsSaving(true);
      await updateTransaction(transaction.id, { status: 'Normal' });
      onSuccess();
      onClose();
    } catch (error) {
      console.error('Error approving transaction:', error);
      alert('Failed to approve transaction. Please try again.');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Edit Transaction</DialogTitle>
          <DialogDescription>
            Update the transaction details below. Click save when you're done.
          </DialogDescription>
        </DialogHeader>

        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          </div>
        ) : (
          <div className="grid gap-4 py-4">
            {/* Date */}
            <div className="grid gap-2">
              <Label htmlFor="date">Date *</Label>
              <Input
                id="date"
                type="date"
                value={formData.date ? formatDateForInput(formData.date) : ''}
                onChange={(e) => setFormData({ ...formData, date: e.target.value })}
              />
            </div>

            {/* Account */}
            <div className="grid gap-2">
              <Label htmlFor="account">Account *</Label>
              <Select
                value={formData.account}
                onValueChange={(value) => setFormData({ ...formData, account: value })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select account" />
                </SelectTrigger>
                <SelectContent>
                  {accounts.map((account) => (
                    <SelectItem key={account} value={account}>
                      {account}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Category */}
            <div className="grid gap-2">
              <Label htmlFor="category">Category *</Label>
              <Select
                value={formData.category}
                onValueChange={(value) => {
                  setFormData({ ...formData, category: value, subcategory: '' });
                }}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select category" />
                </SelectTrigger>
                <SelectContent>
                  {categories.map((category) => (
                    <SelectItem key={category.name} value={category.name}>
                      {category.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Subcategory */}
            {subcategories.length > 0 && (
              <div className="grid gap-2">
                <Label htmlFor="subcategory">Subcategory</Label>
                <Select
                  value={formData.subcategory || ''}
                  onValueChange={(value) => setFormData({ ...formData, subcategory: value })}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select subcategory" />
                  </SelectTrigger>
                  <SelectContent>
                    {subcategories.map((subcategory) => (
                      <SelectItem key={subcategory} value={subcategory}>
                        {subcategory}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}

            {/* Amount */}
            <div className="grid gap-2">
              <Label htmlFor="amount">Amount (IDR) *</Label>
              <Input
                id="amount"
                type="number"
                value={formData.amount || ''}
                onChange={(e) => setFormData({ ...formData, amount: parseFloat(e.target.value) })}
                min="0"
                step="1000"
              />
            </div>

            {/* Description */}
            <div className="grid gap-2">
              <Label htmlFor="description">Description</Label>
              <Input
                id="description"
                value={formData.description || ''}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                placeholder="Optional note"
              />
            </div>

            {/* Status indicator */}
            {transaction?.status === 'Flagged' && (
              <div className="p-3 bg-yellow-50 dark:bg-yellow-950 rounded-lg border border-yellow-200 dark:border-yellow-800">
                <p className="text-sm text-yellow-800 dark:text-yellow-200">
                  This transaction is flagged for review. You can approve it after editing or use the "Approve" button.
                </p>
              </div>
            )}
          </div>
        )}

        <DialogFooter className="gap-2">
          <Button variant="outline" onClick={onClose} disabled={isSaving}>
            Cancel
          </Button>
          {transaction?.status === 'Flagged' && (
            <Button onClick={handleApprove} disabled={isSaving} variant="secondary">
              {isSaving ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Approving...
                </>
              ) : (
                'Approve'
              )}
            </Button>
          )}
          <Button onClick={handleSave} disabled={isSaving || isLoading}>
            {isSaving ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Saving...
              </>
            ) : (
              'Save Changes'
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
