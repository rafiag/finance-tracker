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
import { cn, formatCurrency, getTransactionTypeColor } from "@/lib/utils";
import { Transaction, deleteTransaction, updateTransaction } from "@/lib/services";
import { Edit2, Trash2, CheckCircle, ChevronLeft, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { EditTransactionModal } from "./edit-transaction-modal";
import {
    AlertDialog,
    AlertDialogAction,
    AlertDialogCancel,
    AlertDialogContent,
    AlertDialogDescription,
    AlertDialogFooter,
    AlertDialogHeader,
    AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { toast } from "sonner";
import { TransactionsTableSkeleton } from "@/components/skeletons/transactions-skeleton";

interface TransactionsTableProps {
    transactions: Transaction[];
    isLoading?: boolean;
    onRefresh?: () => void;
}

export function TransactionsTable({ transactions, isLoading, onRefresh }: TransactionsTableProps) {
    const [currentPage, setCurrentPage] = useState(1);
    const [editingTransaction, setEditingTransaction] = useState<Transaction | null>(null);
    const [isEditModalOpen, setIsEditModalOpen] = useState(false);
    const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
    const [transactionToDelete, setTransactionToDelete] = useState<Transaction | null>(null);
    const itemsPerPage = 20;

    if (isLoading) {
        return <TransactionsTableSkeleton />;
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

    const handleEdit = (transaction: Transaction) => {
        setEditingTransaction(transaction);
        setIsEditModalOpen(true);
    };

    const handleApprove = async (transaction: Transaction) => {
        try {
            await updateTransaction(transaction.id, { status: 'Normal' });
            toast.success('Transaction approved successfully');
            if (onRefresh) onRefresh();
        } catch (error) {
            console.error('Error approving transaction:', error);
            toast.error('Failed to approve transaction. Please try again.');
        }
    };

    const handleDeleteClick = (transaction: Transaction) => {
        setTransactionToDelete(transaction);
        setIsDeleteDialogOpen(true);
    };

    const handleDeleteConfirm = async () => {
        if (!transactionToDelete) return;

        try {
            await deleteTransaction(transactionToDelete.id);
            toast.success('Transaction deleted successfully');
            if (onRefresh) onRefresh();
        } catch (error) {
            console.error('Error deleting transaction:', error);
            toast.error('Failed to delete transaction. Please try again.');
        } finally {
            setIsDeleteDialogOpen(false);
            setTransactionToDelete(null);
        }
    };

    const handleEditSuccess = () => {
        if (onRefresh) onRefresh();
        setIsEditModalOpen(false);
        setEditingTransaction(null);
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
                                    getTransactionTypeColor(transaction.type)
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
                                            <Button
                                                variant="ghost"
                                                size="icon"
                                                title="Approve"
                                                onClick={() => handleApprove(transaction)}
                                            >
                                                <CheckCircle className="h-4 w-4 text-green-500" />
                                            </Button>
                                        )}
                                        <Button
                                            variant="ghost"
                                            size="icon"
                                            title="Edit"
                                            onClick={() => handleEdit(transaction)}
                                        >
                                            <Edit2 className="h-4 w-4 text-muted-foreground" />
                                        </Button>
                                        <Button
                                            variant="ghost"
                                            size="icon"
                                            title="Delete"
                                            onClick={() => handleDeleteClick(transaction)}
                                        >
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

            {/* Edit Transaction Modal */}
            <EditTransactionModal
                transaction={editingTransaction}
                isOpen={isEditModalOpen}
                onClose={() => {
                    setIsEditModalOpen(false);
                    setEditingTransaction(null);
                }}
                onSuccess={handleEditSuccess}
            />

            {/* Delete Confirmation Dialog */}
            <AlertDialog open={isDeleteDialogOpen} onOpenChange={setIsDeleteDialogOpen}>
                <AlertDialogContent>
                    <AlertDialogHeader>
                        <AlertDialogTitle>Delete Transaction</AlertDialogTitle>
                        <AlertDialogDescription>
                            Are you sure you want to delete this transaction?
                            <br />
                            <br />
                            <strong>{transactionToDelete?.description || 'No description'}</strong>
                            <br />
                            Amount: {transactionToDelete && formatCurrency(transactionToDelete.amount)}
                            <br />
                            Date: {transactionToDelete && new Date(transactionToDelete.date).toLocaleDateString()}
                        </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                        <AlertDialogCancel>Cancel</AlertDialogCancel>
                        <AlertDialogAction
                            onClick={handleDeleteConfirm}
                            className="bg-red-500 hover:bg-red-600"
                        >
                            Delete
                        </AlertDialogAction>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>
        </div>
    );
}
