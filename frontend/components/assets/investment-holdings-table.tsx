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
import { Badge } from '@/components/ui/badge';
import { Investment, MarketData, fetchMarketData } from '@/lib/services';
import {
  formatCurrency,
  formatPercentage,
  getProfitLossColor,
  calculateProfitLoss,
} from '@/lib/utils';
import { RefreshCw, TrendingUp, TrendingDown } from 'lucide-react';

interface InvestmentHoldingsTableProps {
  investments: Investment[];
  isLoading?: boolean;
  onRefresh?: () => void;
}

interface EnrichedInvestment extends Investment {
  currentPrice?: number;
  marketValue?: number;
  profitLoss?: number;
  profitLossPercentage?: number;
  priceChange?: number;
}

export function InvestmentHoldingsTable({
  investments,
  isLoading,
  onRefresh,
}: InvestmentHoldingsTableProps) {
  const [enrichedInvestments, setEnrichedInvestments] = useState<EnrichedInvestment[]>([]);
  const [isLoadingMarketData, setIsLoadingMarketData] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  useEffect(() => {
    if (investments.length > 0) {
      loadMarketData();
    } else {
      setEnrichedInvestments([]);
    }
  }, [investments]);

  async function loadMarketData() {
    try {
      setIsLoadingMarketData(true);

      // Get unique symbols
      const symbols = [...new Set(investments.map(inv => inv.symbol))];

      if (symbols.length === 0) {
        setEnrichedInvestments(investments);
        return;
      }

      // Fetch market data
      const marketData = await fetchMarketData(symbols);

      // Enrich investments with market data
      const enriched: EnrichedInvestment[] = investments.map(inv => {
        const market = marketData[inv.symbol];

        if (!market) {
          return inv;
        }

        // Handle currency conversion
        const exchangeRate = inv.exchange_rate || 1;
        const avgPriceIDR = inv.avg_price * exchangeRate;
        const currentPriceIDR = market.current_price * exchangeRate;
        const marketValue = currentPriceIDR * inv.shares;

        // Calculate P/L
        const { amount: profitLoss, percentage: profitLossPercentage } = calculateProfitLoss(
          currentPriceIDR,
          avgPriceIDR,
          inv.shares
        );

        return {
          ...inv,
          currentPrice: currentPriceIDR,
          marketValue,
          profitLoss,
          profitLossPercentage,
          priceChange: market.change_percent,
        };
      });

      setEnrichedInvestments(enriched);
      setLastUpdated(new Date());
    } catch (error) {
      console.error('Error loading market data:', error);
      setEnrichedInvestments(investments);
    } finally {
      setIsLoadingMarketData(false);
    }
  }

  if (isLoading) {
    return <div className="p-4 text-center">Loading investments...</div>;
  }

  if (investments.length === 0) {
    return (
      <div className="p-8 text-center border rounded-lg bg-muted/20">
        No investment holdings found. Add your first stock to get started.
      </div>
    );
  }

  // Calculate totals
  const totalCost = enrichedInvestments.reduce(
    (sum, inv) => sum + inv.avg_price * inv.shares * (inv.exchange_rate || 1),
    0
  );
  const totalMarketValue = enrichedInvestments.reduce(
    (sum, inv) => sum + (inv.marketValue || inv.avg_price * inv.shares * (inv.exchange_rate || 1)),
    0
  );
  const totalProfitLoss = totalMarketValue - totalCost;
  const totalProfitLossPercentage = totalCost > 0 ? (totalProfitLoss / totalCost) * 100 : 0;

  return (
    <div className="space-y-4">
      {/* Header with Refresh */}
      <div className="flex items-center justify-between">
        <div className="space-y-1">
          <p className="text-sm text-muted-foreground">Total Portfolio Value</p>
          <p className="text-2xl font-bold">{formatCurrency(totalMarketValue)}</p>
          <div className={`flex items-center gap-2 text-sm font-medium ${getProfitLossColor(totalProfitLoss)}`}>
            {totalProfitLoss >= 0 ? (
              <TrendingUp className="h-4 w-4" />
            ) : (
              <TrendingDown className="h-4 w-4" />
            )}
            <span>
              {totalProfitLoss >= 0 ? '+' : ''}
              {formatCurrency(totalProfitLoss)} ({formatPercentage(totalProfitLossPercentage)})
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {lastUpdated && (
            <p className="text-xs text-muted-foreground">
              Updated: {lastUpdated.toLocaleTimeString()}
            </p>
          )}
          <Button
            variant="outline"
            size="sm"
            onClick={loadMarketData}
            disabled={isLoadingMarketData}
            className="gap-2"
          >
            <RefreshCw className={`h-4 w-4 ${isLoadingMarketData ? 'animate-spin' : ''}`} />
            Refresh Prices
          </Button>
        </div>
      </div>

      {/* Table */}
      <div className="rounded-md border bg-card overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Symbol</TableHead>
              <TableHead>Account</TableHead>
              <TableHead className="text-right">Shares</TableHead>
              <TableHead className="text-right">Avg. Buy Price</TableHead>
              <TableHead className="text-right">Current Price</TableHead>
              <TableHead className="text-right">Market Value</TableHead>
              <TableHead className="text-right">P/L</TableHead>
              <TableHead className="text-right">P/L %</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {enrichedInvestments.map((inv, idx) => {
              const exchangeRate = inv.exchange_rate || 1;
              const avgPriceIDR = inv.avg_price * exchangeRate;
              const marketValue = inv.marketValue || avgPriceIDR * inv.shares;
              const costBasis = avgPriceIDR * inv.shares;

              return (
                <TableRow key={`${inv.symbol}-${idx}`}>
                  <TableCell className="font-medium">
                    <div className="flex flex-col">
                      <span>{inv.symbol}</span>
                      {inv.currency !== 'IDR' && (
                        <Badge variant="outline" className="w-fit text-xs mt-1">
                          {inv.currency}
                        </Badge>
                      )}
                    </div>
                  </TableCell>
                  <TableCell>{inv.account}</TableCell>
                  <TableCell className="text-right">{inv.shares.toFixed(4)}</TableCell>
                  <TableCell className="text-right">
                    {inv.currency === 'USD' ? (
                      <div className="flex flex-col items-end">
                        <span className="text-xs text-muted-foreground">
                          ${inv.avg_price.toFixed(2)}
                        </span>
                        <span>{formatCurrency(avgPriceIDR)}</span>
                      </div>
                    ) : (
                      formatCurrency(avgPriceIDR)
                    )}
                  </TableCell>
                  <TableCell className="text-right">
                    {inv.currentPrice ? (
                      <div className="flex flex-col items-end">
                        <span>{formatCurrency(inv.currentPrice)}</span>
                        {inv.priceChange && (
                          <span className={`text-xs ${getProfitLossColor(inv.priceChange)}`}>
                            {inv.priceChange >= 0 ? '+' : ''}
                            {formatPercentage(inv.priceChange)}
                          </span>
                        )}
                      </div>
                    ) : (
                      <span className="text-muted-foreground">-</span>
                    )}
                  </TableCell>
                  <TableCell className="text-right font-medium">
                    {formatCurrency(marketValue)}
                  </TableCell>
                  <TableCell className={`text-right font-medium ${getProfitLossColor(inv.profitLoss || 0)}`}>
                    {inv.profitLoss !== undefined ? (
                      <>
                        {inv.profitLoss >= 0 ? '+' : ''}
                        {formatCurrency(inv.profitLoss)}
                      </>
                    ) : (
                      '-'
                    )}
                  </TableCell>
                  <TableCell className={`text-right font-medium ${getProfitLossColor(inv.profitLossPercentage || 0)}`}>
                    {inv.profitLossPercentage !== undefined ? (
                      <>
                        {inv.profitLossPercentage >= 0 ? '+' : ''}
                        {formatPercentage(inv.profitLossPercentage)}
                      </>
                    ) : (
                      '-'
                    )}
                  </TableCell>
                </TableRow>
              );
            })}

            {/* Totals Row */}
            <TableRow className="bg-muted/50 font-bold">
              <TableCell colSpan={5}>Total</TableCell>
              <TableCell className="text-right">{formatCurrency(totalMarketValue)}</TableCell>
              <TableCell className={`text-right ${getProfitLossColor(totalProfitLoss)}`}>
                {totalProfitLoss >= 0 ? '+' : ''}
                {formatCurrency(totalProfitLoss)}
              </TableCell>
              <TableCell className={`text-right ${getProfitLossColor(totalProfitLossPercentage)}`}>
                {totalProfitLossPercentage >= 0 ? '+' : ''}
                {formatPercentage(totalProfitLossPercentage)}
              </TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </div>

      <p className="text-xs text-muted-foreground">
        * Market prices are fetched in real-time. Click "Refresh Prices" to update.
      </p>
    </div>
  );
}
