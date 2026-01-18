import { useState } from "react";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { cn, formatCurrency } from "@/lib/utils";
import { Transaction } from "@/lib/services";
import { Edit2, Trash2, CheckCircle, ChevronLeft, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";

interface TransactionsTableProps {
    transactions: Transaction[];
    isLoading?: boolean;
}

export function TransactionsTable({ transactions, isLoading }: TransactionsTableProps) {
    const [currentPage, setCurrentPage] = useState(1);
    const itemsPerPage = 20;

    if (isLoading) {
        return <div className="p-4 text-center">Loading transactions...</div>;
    }

    if (transactions.length === 0) {
        return <div className="p-8 text-center border rounded-lg bg-muted/20">No transactions found.</div>;
    }

    const totalPages = Math.ceil(transactions.length / itemsPerPage);
    const startIndex = (currentPage - 1) * itemsPerPage;
    const paginatedTransactions = transactions.slice(startIndex, startIndex + itemsPerPage);

    const handlePrevious = () => {
        if (currentPage > 1) setCurrentPage(currentPage - 1);
    };

    const handleNext = () => {
        if (currentPage < totalPages) setCurrentPage(currentPage + 1);
    };

    return (
        <div className="space-y-4">
            <div className="rounded-md border bg-card">
                <Table>
                    <TableHeader>
                        <TableRow>
                            <TableHead className="w-[100px]">Date</TableHead>
                            <TableHead>Account</TableHead>
                            <TableHead>Category</TableHead>
                            <TableHead className="max-w-[300px]">Description</TableHead>
                            <TableHead className="text-right">Amount</TableHead>
                            <TableHead className="w-[100px]">Status</TableHead>
                            <TableHead className="text-right">Actions</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {paginatedTransactions.map((transaction) => (
                            <TableRow key={transaction.id}>
                                <TableCell className="font-medium">
                                    {new Date(transaction.date).toLocaleDateString()}
                                </TableCell>
                                <TableCell>{transaction.account}</TableCell>
                                <TableCell>
                                    <div className="flex flex-col">
                                        <span>{transaction.category}</span>
                                        {transaction.subcategory && (
                                            <span className="text-xs text-muted-foreground">{transaction.subcategory}</span>
                                        )}
                                    </div>
                                </TableCell>
                                <TableCell className="truncate max-w-[300px]" title={transaction.description}>
                                    {transaction.description}
                                </TableCell>
                                <TableCell className={cn(
                                    "text-right font-medium",
                                    transaction.type === 'Income' ? "text-income-600 dark:text-income-400" :
                                        transaction.type === 'Expense' ? "text-expense-600 dark:text-expense-400" : ""
                                )}>
                                    {transaction.type === 'Income' ? '+' : '-'}{formatCurrency(Math.abs(transaction.amount))}
                                </TableCell>
                                <TableCell>
                                    {transaction.status === 'Flagged' ? (
                                        <Badge variant="destructive" className="bg-yellow-500 hover:bg-yellow-600">Flagged</Badge>
                                    ) : (
                                        <Badge variant="outline" className="text-muted-foreground">Normal</Badge>
                                    )}
                                </TableCell>
                                <TableCell className="text-right">
                                    <div className="flex justify-end gap-2">
                                        {transaction.status === 'Flagged' && (
                                            <Button variant="ghost" size="icon" title="Approve">
                                                <CheckCircle className="h-4 w-4 text-green-500" />
                                            </Button>
                                        )}
                                        <Button variant="ghost" size="icon" title="Edit">
                                            <Edit2 className="h-4 w-4 text-muted-foreground" />
                                        </Button>
                                        <Button variant="ghost" size="icon" title="Delete">
                                            <Trash2 className="h-4 w-4 text-muted-foreground" />
                                        </Button>
                                    </div>
                                </TableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            </div>

            {totalPages > 1 && (
                <div className="flex items-center justify-end space-x-2 py-4">
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={handlePrevious}
                        disabled={currentPage === 1}
                    >
                        <ChevronLeft className="h-4 w-4 mr-1" />
                        Previous
                    </Button>
                    <div className="text-sm text-muted-foreground">
                        Page {currentPage} of {totalPages}
                    </div>
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={handleNext}
                        disabled={currentPage === totalPages}
                    >
                        Next
                        <ChevronRight className="h-4 w-4 ml-1" />
                    </Button>
                </div>
            )}
        </div>
    );
}
