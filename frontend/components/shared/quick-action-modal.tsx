"use client";

import { useState, useEffect, useMemo } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { createTransaction, createInvestment, Account, Transaction, fetchAccounts, fetchCategories, Category } from "@/lib/services";
import { useRouter } from "next/navigation";

interface QuickActionModalProps {
    children: React.ReactNode;
    onSuccess?: () => void;
}

export function QuickActionModal({ children, onSuccess }: QuickActionModalProps) {
    const [open, setOpen] = useState(false);
    const [activeTab, setActiveTab] = useState<Transaction['type']>("Expense");
    const [loading, setLoading] = useState(false);
    const [accounts, setAccounts] = useState<Account[]>([]);
    const [categories, setCategories] = useState<Category[]>([]);

    // Form states
    const [formData, setFormData] = useState({
        date: new Date().toISOString().split('T')[0],
        amount: "",
        description: "",
        account: "",
        category: "",
        subcategory: "",
        // Transfer specific
        toAccount: "",
        // Investment specific
        symbol: "",
        price: "",
        currency: "IDR"
    });

    const router = useRouter(); // Initialized useRouter
    const [feedback, setFeedback] = useState<{ message: string, type: 'success' | 'error' } | null>(null);

    useEffect(() => {
        if (open) {
            fetchAccounts().then(setAccounts);
            fetchCategories().then(setCategories);
        }
    }, [open]);

    // Get unique categories for current type
    const availableCategories = useMemo(() => {
        const type = activeTab === 'Stock' ? 'Investment' : activeTab; // Map 'Stock' tab to 'Investment' type if needed, though backend uses 'Asset'
        // Actually backend Category sheet has 'Expense' 'Income' types. 
        // For 'Investment'/Stock, we might not need category picker or use 'Investment'

        const filtered = categories.filter(c => c.type === type);
        const unique = Array.from(new Set(filtered.map(c => c.category)));
        return unique.sort();
    }, [categories, activeTab]);

    // Get subcategories for selected category
    const availableSubcategories = useMemo(() => {
        if (!formData.category) return [];
        return categories
            .filter(c => c.category === formData.category && c.type === activeTab)
            .map(c => c.subcategory)
            .sort();
    }, [categories, formData.category, activeTab]);

    // Validation Logic
    const isFormValid = useMemo(() => {
        const { date, amount, account } = formData;
        if (!date || !amount) return false;

        switch (activeTab) {
            case 'Expense':
            case 'Income':
                return !!account && !!formData.category && !!formData.subcategory;
            case 'Transfer':
                return !!account && !!formData.toAccount;
            case 'Stock': // Investment
                return !!account && !!formData.symbol && !!formData.price;
            default:
                return false;
        }
    }, [formData, activeTab]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setFeedback(null); // Clear previous feedback

        try {
            const amountVal = parseFloat(formData.amount);
            const priceVal = parseFloat(formData.price);

            if (activeTab === 'Stock') {
                await createInvestment({
                    symbol: formData.symbol,
                    amount: amountVal, // IDR amount
                    price: priceVal, // Price per share (USD or IDR)
                    account: formData.account,
                    currency: formData.currency as "IDR" | "USD",
                    date: formData.date
                });
            } else {
                // Regular Transaction
                const payload: any = {
                    date: formData.date,
                    amount: amountVal,
                    description: formData.description,
                    account: formData.account,
                    category: formData.category,
                    type: activeTab,
                    subcategory: formData.subcategory,
                };

                if (activeTab === 'Transfer') {
                    payload.description = `Transfer to ${formData.toAccount}`;
                }

                await createTransaction(payload);
            }

            setFeedback({ message: "Transaction saved successfully!", type: 'success' });

            // Initial clear of form data but keep modal open briefly for feedback
            setFormData({ ...formData, amount: "", description: "", category: "", subcategory: "", symbol: "", price: "" });
            router.refresh();
            if (onSuccess) onSuccess();

            // Close after delay
            setTimeout(() => {
                setOpen(false);
            }, 1000);

        } catch (error) {
            console.error("Failed to create transaction", error);
            setFeedback({ message: "Failed to create transaction. Please try again.", type: 'error' });
        } finally {
            setLoading(false);
        }
    };

    return (
        <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>
                {children}
            </DialogTrigger>
            <DialogContent className="sm:max-w-[600px]">
                <DialogHeader>
                    <DialogTitle>Add New Transaction</DialogTitle>
                </DialogHeader>

                <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as Transaction['type'])} className="w-full">
                    <TabsList className="grid w-full grid-cols-4 mb-4">
                        <TabsTrigger value="Expense">Expense</TabsTrigger>
                        <TabsTrigger value="Income">Income</TabsTrigger>
                        <TabsTrigger value="Transfer">Transfer</TabsTrigger>
                        <TabsTrigger value="Stock">Investment</TabsTrigger>
                    </TabsList>

                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label htmlFor="date">Date</Label>
                                <Input
                                    id="date"
                                    type="date"
                                    value={formData.date}
                                    onChange={(e) => setFormData({ ...formData, date: e.target.value })}
                                    required
                                />
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="amount">Amount (IDR)</Label>
                                <Input
                                    id="amount"
                                    type="number"
                                    placeholder="0"
                                    value={formData.amount}
                                    onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
                                    required
                                />
                            </div>
                        </div>

                        {activeTab === 'Transfer' ? (
                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-2">
                                    <Label htmlFor="account">From Account</Label>
                                    <Select
                                        value={formData.account}
                                        onValueChange={(v) => setFormData({ ...formData, account: v })}
                                        required
                                    >
                                        <SelectTrigger>
                                            <SelectValue placeholder="Select account" />
                                        </SelectTrigger>
                                        <SelectContent>
                                            {accounts.map(acc => (
                                                <SelectItem key={acc.name} value={acc.name}>{acc.name}</SelectItem>
                                            ))}
                                        </SelectContent>
                                    </Select>
                                </div>
                                <div className="space-y-2">
                                    <Label htmlFor="toAccount">To Account</Label>
                                    <Select
                                        value={formData.toAccount}
                                        onValueChange={(v) => setFormData({ ...formData, toAccount: v })}
                                        required
                                    >
                                        <SelectTrigger>
                                            <SelectValue placeholder="Select account" />
                                        </SelectTrigger>
                                        <SelectContent>
                                            {accounts.map(acc => (
                                                <SelectItem key={acc.name} value={acc.name}>{acc.name}</SelectItem>
                                            ))}
                                        </SelectContent>
                                    </Select>
                                </div>
                            </div>
                        ) : activeTab === 'Stock' ? (
                            <>
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="space-y-2">
                                        <Label htmlFor="account">Account</Label>
                                        <Select
                                            value={formData.account}
                                            onValueChange={(v) => setFormData({ ...formData, account: v })}
                                            required
                                        >
                                            <SelectTrigger>
                                                <SelectValue placeholder="Select account" />
                                            </SelectTrigger>
                                            <SelectContent>
                                                {accounts.filter(a => a.type === 'Investment').map(acc => (
                                                    <SelectItem key={acc.name} value={acc.name}>{acc.name}</SelectItem>
                                                ))}
                                            </SelectContent>
                                        </Select>
                                    </div>
                                    <div className="space-y-2">
                                        <Label htmlFor="symbol">Symbol</Label>
                                        <Input
                                            id="symbol"
                                            placeholder="AAPL"
                                            value={formData.symbol}
                                            onChange={(e) => setFormData({ ...formData, symbol: e.target.value.toUpperCase() })}
                                            required
                                        />
                                    </div>
                                </div>
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="space-y-2">
                                        <Label htmlFor="price">Price per Share</Label>
                                        <Input
                                            id="price"
                                            type="number"
                                            placeholder="0.00"
                                            value={formData.price}
                                            onChange={(e) => setFormData({ ...formData, price: e.target.value })}
                                            required
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <Label>Currency</Label>
                                        <div className="flex bg-muted rounded-md p-1">
                                            <Button
                                                type="button"
                                                variant={formData.currency === 'IDR' ? 'default' : 'ghost'}
                                                className="flex-1 h-8 text-xs"
                                                onClick={() => setFormData({ ...formData, currency: 'IDR' })}
                                            >
                                                IDR
                                            </Button>
                                            <Button
                                                type="button"
                                                variant={formData.currency === 'USD' ? 'default' : 'ghost'}
                                                className="flex-1 h-8 text-xs"
                                                onClick={() => setFormData({ ...formData, currency: 'USD' })}
                                            >
                                                USD
                                            </Button>
                                        </div>
                                    </div>
                                </div>
                                <div className="text-xs text-muted-foreground">
                                    Shares will be automatically calculated based on Amount (IDR) / Price ({formData.currency}).
                                </div>
                            </>
                        ) : (
                            <>
                                <div className="space-y-2">
                                    <Label htmlFor="account">Account</Label>
                                    <Select
                                        value={formData.account}
                                        onValueChange={(v) => setFormData({ ...formData, account: v })}
                                        required
                                    >
                                        <SelectTrigger>
                                            <SelectValue placeholder="Select account" />
                                        </SelectTrigger>
                                        <SelectContent>
                                            {accounts.map(acc => (
                                                <SelectItem key={acc.name} value={acc.name}>{acc.name}</SelectItem>
                                            ))}
                                        </SelectContent>
                                    </Select>
                                </div>
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="space-y-2">
                                        <Label htmlFor="category">Category</Label>
                                        <Select
                                            value={formData.category}
                                            onValueChange={(v) => setFormData({ ...formData, category: v, subcategory: "" })}
                                            required
                                        >
                                            <SelectTrigger>
                                                <SelectValue placeholder="Select category" />
                                            </SelectTrigger>
                                            <SelectContent>
                                                {availableCategories.map(cat => (
                                                    <SelectItem key={cat} value={cat}>{cat}</SelectItem>
                                                ))}
                                            </SelectContent>
                                        </Select>
                                    </div>
                                    <div className="space-y-2">
                                        <Label htmlFor="subcategory">Subcategory</Label>
                                        <Select
                                            value={formData.subcategory}
                                            onValueChange={(v) => setFormData({ ...formData, subcategory: v })}
                                            disabled={!formData.category}
                                        >
                                            <SelectTrigger>
                                                <SelectValue placeholder="Select subcategory" />
                                            </SelectTrigger>
                                            <SelectContent>
                                                {availableSubcategories.map(sub => (
                                                    <SelectItem key={sub} value={sub}>{sub}</SelectItem>
                                                ))}
                                            </SelectContent>
                                        </Select>
                                    </div>
                                </div>
                            </>
                        )}

                        <div className="space-y-2">
                            <Label htmlFor="description">Description</Label>
                            <Input
                                id="description"
                                placeholder="Optional note"
                                value={formData.description}
                                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                            />
                        </div>

                        {feedback && (
                            <div className={`text-sm p-2 rounded-md ${feedback.type === 'success' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                                {feedback.message}
                            </div>
                        )}

                        <Button type="submit" className="w-full" disabled={loading || (feedback?.type === 'success') || !isFormValid}>
                            {loading ? "Saving..." : (feedback?.type === 'success' ? "Saved!" : "Save Transaction")}
                        </Button>
                    </form>
                </Tabs>
            </DialogContent>
        </Dialog>
    );
}
