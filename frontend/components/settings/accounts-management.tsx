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
import { Label } from '@/components/ui/label';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  fetchAccounts,
  createAccount,
  updateAccount,
  deleteAccount,
  Account,
} from '@/lib/services';
import { formatCurrency } from '@/lib/utils';
import { Plus, Edit2, Trash2, Loader2 } from 'lucide-react';

export function AccountsManagement() {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalMode, setModalMode] = useState<'create' | 'edit'>('create');
  const [selectedAccount, setSelectedAccount] = useState<Account | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  // Form state
  const [formData, setFormData] = useState({
    name: '',
    type: 'Bank',
    currency: 'IDR',
    balance: 0,
  });

  useEffect(() => {
    loadAccounts();
  }, []);

  async function loadAccounts() {
    try {
      setIsLoading(true);
      const data = await fetchAccounts();
      setAccounts(data);
    } catch (error) {
      console.error('Error loading accounts:', error);
      alert('Failed to load accounts');
    } finally {
      setIsLoading(false);
    }
  }

  const handleCreate = () => {
    setModalMode('create');
    setFormData({ name: '', type: 'Bank', currency: 'IDR', balance: 0 });
    setSelectedAccount(null);
    setIsModalOpen(true);
  };

  const handleEdit = (account: Account) => {
    setModalMode('edit');
    setFormData({
      name: account.name,
      type: account.type,
      currency: account.currency,
      balance: account.balance,
    });
    setSelectedAccount(account);
    setIsModalOpen(true);
  };

  const handleDelete = async (account: Account) => {
    const confirmed = window.confirm(
      `Are you sure you want to delete account "${account.name}"?\n\n` +
        `All transactions using this account will be reassigned to "Uncategorized".`
    );

    if (!confirmed) return;

    try {
      await deleteAccount(account.name);
      alert(`Account "${account.name}" deleted successfully`);
      loadAccounts();
    } catch (error) {
      console.error('Error deleting account:', error);
      alert('Failed to delete account');
    }
  };

  const handleSave = async () => {
    try {
      setIsSaving(true);

      if (modalMode === 'create') {
        await createAccount({
          name: formData.name,
          type: formData.type,
          currency: formData.currency,
        });
        alert(`Account "${formData.name}" created successfully`);
      } else {
        // Edit mode
        const updates: any = {};

        if (formData.name !== selectedAccount?.name) {
          updates.new_name = formData.name;
        }

        if (formData.type !== selectedAccount?.type) {
          updates.type = formData.type;
        }

        // Balance update only for non-investment accounts
        if (
          selectedAccount?.type !== 'Investment' &&
          formData.balance !== selectedAccount?.balance
        ) {
          updates.balance = formData.balance;
        }

        if (Object.keys(updates).length > 0) {
          const result = await updateAccount(selectedAccount!.name, updates);

          if (result.balance_adjusted) {
            const adjustment = result.adjustment_amount!;
            alert(
              `Account updated successfully.\n\n` +
                `Balance adjustment transaction created: ${
                  adjustment > 0 ? '+' : ''
                }${formatCurrency(adjustment)}`
            );
          } else {
            alert('Account updated successfully');
          }
        }
      }

      setIsModalOpen(false);
      loadAccounts();
    } catch (error: any) {
      console.error('Error saving account:', error);
      alert(error?.message || 'Failed to save account');
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return <div className="p-8 text-center">Loading accounts...</div>;
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <Button onClick={handleCreate} className="gap-2">
          <Plus className="h-4 w-4" />
          Add Account
        </Button>
      </div>

      <div className="rounded-md border bg-card">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Account Name</TableHead>
              <TableHead>Type</TableHead>
              <TableHead>Currency</TableHead>
              <TableHead className="text-right">Balance</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {accounts.length === 0 ? (
              <TableRow>
                <TableCell colSpan={5} className="text-center text-muted-foreground">
                  No accounts found. Create your first account to get started.
                </TableCell>
              </TableRow>
            ) : (
              accounts.map((account) => (
                <TableRow key={account.name}>
                  <TableCell className="font-medium">{account.name}</TableCell>
                  <TableCell>{account.type}</TableCell>
                  <TableCell>{account.currency}</TableCell>
                  <TableCell className="text-right font-medium">
                    {formatCurrency(account.balance, account.currency)}
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex justify-end gap-2">
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => handleEdit(account)}
                        title="Edit"
                      >
                        <Edit2 className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => handleDelete(account)}
                        title="Delete"
                      >
                        <Trash2 className="h-4 w-4 text-red-500" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      {/* Add/Edit Modal */}
      <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {modalMode === 'create' ? 'Add New Account' : 'Edit Account'}
            </DialogTitle>
            <DialogDescription>
              {modalMode === 'create'
                ? 'Create a new account to track your finances.'
                : 'Update account details. Balance adjustments will create automatic transactions.'}
            </DialogDescription>
          </DialogHeader>

          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="account-name">Account Name *</Label>
              <Input
                id="account-name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="e.g., BCA, Cash, Gopay"
              />
            </div>

            <div className="grid gap-2">
              <Label htmlFor="account-type">Type *</Label>
              <Select
                value={formData.type}
                onValueChange={(value) => setFormData({ ...formData, type: value })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="Bank">Bank</SelectItem>
                  <SelectItem value="Cash">Cash</SelectItem>
                  <SelectItem value="E-wallet">E-wallet</SelectItem>
                  <SelectItem value="Investment">Investment</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="grid gap-2">
              <Label htmlFor="currency">Currency *</Label>
              <Select
                value={formData.currency}
                onValueChange={(value) => setFormData({ ...formData, currency: value })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="IDR">IDR (Indonesian Rupiah)</SelectItem>
                  <SelectItem value="USD">USD (US Dollar)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {modalMode === 'edit' && selectedAccount?.type !== 'Investment' && (
              <div className="grid gap-2">
                <Label htmlFor="balance">Current Balance</Label>
                <Input
                  id="balance"
                  type="number"
                  value={formData.balance}
                  onChange={(e) =>
                    setFormData({ ...formData, balance: parseFloat(e.target.value) })
                  }
                  step="1000"
                />
                <p className="text-xs text-muted-foreground">
                  Changing the balance will create an automatic adjustment transaction.
                </p>
              </div>
            )}

            {modalMode === 'edit' && selectedAccount?.type === 'Investment' && (
              <p className="text-sm text-muted-foreground">
                Note: Balance cannot be manually adjusted for investment accounts.
              </p>
            )}
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setIsModalOpen(false)} disabled={isSaving}>
              Cancel
            </Button>
            <Button onClick={handleSave} disabled={isSaving || !formData.name}>
              {isSaving ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Saving...
                </>
              ) : modalMode === 'create' ? (
                'Create Account'
              ) : (
                'Save Changes'
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
