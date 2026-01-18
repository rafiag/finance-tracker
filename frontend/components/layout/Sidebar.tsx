import Link from 'next/link';
import { LayoutDashboard, PieChart, Wallet, ArrowRightLeft, Settings, Plus } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { QuickActionModal } from '@/components/shared/quick-action-modal';

const menuItems = [
    { icon: LayoutDashboard, label: 'Dashboard', href: '/' },
    { icon: Wallet, label: 'Assets', href: '/assets' },
    { icon: PieChart, label: 'Budget', href: '/budget' },
    { icon: ArrowRightLeft, label: 'Transactions', href: '/transactions' },
    { icon: Settings, label: 'Settings', href: '/settings' },
];

export function Sidebar() {
    return (
        <div className="w-64 border-r bg-sidebar h-screen fixed left-0 top-0 flex flex-col p-4 text-sidebar-foreground">
            <div className="mb-8 px-2">
                <h1 className="text-xl font-bold">Finance Tracker</h1>
            </div>

            <nav className="flex-1 space-y-2">
                {menuItems.map((item) => (
                    <Link
                        key={item.href}
                        href={item.href}
                        className={cn(
                            "flex items-center gap-3 px-3 py-2 rounded-md hover:bg-sidebar-accent hover:text-sidebar-accent-foreground transition-colors",
                            // Add active state logic here if needed, or use usePathname hook
                        )}
                    >
                        <item.icon className="w-5 h-5" />
                        <span>{item.label}</span>
                    </Link>
                ))}
            </nav>

            <div className="pt-4 mt-auto">
                <QuickActionModal>
                    <Button className="w-full gap-2 bg-primary text-primary-foreground hover:bg-primary/90">
                        <Plus className="w-4 h-4" />
                        Add Transaction
                    </Button>
                </QuickActionModal>
            </div>
        </div>
    );
}
