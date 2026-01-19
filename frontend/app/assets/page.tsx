'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Plus } from 'lucide-react';
import { NetWorthChart } from '@/components/assets/net-worth-chart';
import { TransactionAccountsTable } from '@/components/assets/transaction-accounts-table';
import { InvestmentHoldingsTable } from '@/components/assets/investment-holdings-table';
import { QuickActionModal } from '@/components/shared/quick-action-modal';
import { fetchAccountBalances, fetchInvestments, Account, Investment } from '@/lib/services';

export default function AssetsPage() {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [investments, setInvestments] = useState<Investment[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalTab, setModalTab] = useState<'expense' | 'income' | 'transfer' | 'stock'>('stock');

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    try {
      setIsLoading(true);
      const [accountsData, investmentsData] = await Promise.all([
        fetchAccountBalances(),
        fetchInvestments(),
      ]);

      // Transform account balances to Account type
      const transformedAccounts: Account[] = accountsData.map(ab => ({
        name: ab.account,
        type: ab.type as any,
        balance: ab.balance,
        currency: 'IDR',
      }));

      setAccounts(transformedAccounts);
      setInvestments(investmentsData);
    } catch (error) {
      console.error('Error loading assets data:', error);
    } finally {
      setIsLoading(false);
    }
  }

  const handleAddStock = () => {
    setModalTab('stock');
    setIsModalOpen(true);
  };

  const handleModalSuccess = () => {
    setIsModalOpen(false);
    loadData(); // Reload data after successful creation
  };

  // Calculate net worth
  const transactionAccountsBalance = accounts
    .filter(a => a.type !== 'Investment')
    .reduce((sum, a) => sum + a.balance, 0);

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Assets & Portfolio</h1>
        <Button onClick={handleAddStock} className="gap-2">
          <Plus className="h-4 w-4" />
          Add Stock
        </Button>
      </div>

      {/* Net Worth Overview */}
      <Card>
        <CardHeader>
          <CardTitle>Net Worth Overview</CardTitle>
        </CardHeader>
        <CardContent>
          <NetWorthChart accounts={accounts} investments={investments} />
        </CardContent>
      </Card>

      {/* Transaction Accounts */}
      <Card>
        <CardHeader>
          <CardTitle>Transaction Accounts</CardTitle>
        </CardHeader>
        <CardContent>
          <TransactionAccountsTable
            accounts={accounts.filter(a => a.type !== 'Investment')}
            isLoading={isLoading}
          />
        </CardContent>
      </Card>

      {/* Investment Holdings */}
      <Card>
        <CardHeader>
          <CardTitle>Investment Holdings</CardTitle>
        </CardHeader>
        <CardContent>
          <InvestmentHoldingsTable
            investments={investments}
            isLoading={isLoading}
            onRefresh={loadData}
          />
        </CardContent>
      </Card>

      {/* Quick Action Modal */}
      <QuickActionModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        defaultTab={modalTab}
        onSuccess={handleModalSuccess}
      />
    </div>
  );
}
