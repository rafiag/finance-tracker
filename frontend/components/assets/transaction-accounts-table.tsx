'use client';

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Account } from '@/lib/services';
import { formatCurrency, getCurrentYearMonth } from '@/lib/utils';
import { Wallet, Building2, Smartphone } from 'lucide-react';

interface TransactionAccountsTableProps {
  accounts: Account[];
  isLoading?: boolean;
}

function getAccountIcon(type: string) {
  switch (type) {
    case 'Bank':
      return <Building2 className="h-4 w-4 text-blue-500" />;
    case 'E-wallet':
      return <Smartphone className="h-4 w-4 text-purple-500" />;
    case 'Cash':
      return <Wallet className="h-4 w-4 text-green-500" />;
    default:
      return <Wallet className="h-4 w-4" />;
  }
}

export function TransactionAccountsTable({ accounts, isLoading }: TransactionAccountsTableProps) {
  if (isLoading) {
    return <div className="p-4 text-center">Loading accounts...</div>;
  }

  if (accounts.length === 0) {
    return (
      <div className="p-8 text-center border rounded-lg bg-muted/20">
        No transaction accounts found.
      </div>
    );
  }

  // Calculate total balance
  const totalBalance = accounts.reduce((sum, account) => sum + account.balance, 0);

  return (
    <div className="space-y-4">
      {/* Summary */}
      <div className="flex items-center justify-between p-4 bg-muted/20 rounded-lg">
        <span className="text-sm font-medium">Total Balance</span>
        <span className="text-2xl font-bold">{formatCurrency(totalBalance)}</span>
      </div>

      {/* Table */}
      <div className="rounded-md border bg-card">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Account Name</TableHead>
              <TableHead>Type</TableHead>
              <TableHead className="text-right">Current Balance</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {accounts.map((account) => (
              <TableRow key={account.name}>
                <TableCell className="font-medium">
                  <div className="flex items-center gap-2">
                    {getAccountIcon(account.type)}
                    {account.name}
                  </div>
                </TableCell>
                <TableCell>{account.type}</TableCell>
                <TableCell className="text-right font-medium">
                  {formatCurrency(account.balance)}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
