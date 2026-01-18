import { Calendar } from 'lucide-react';
import { Button } from '@/components/ui/button';

export function Header() {
    return (
        <header className="h-16 border-b px-6 flex items-center justify-between bg-background sticky top-0 z-10">
            <h2 className="text-lg font-semibold">Dashboard</h2>

            <div className="flex items-center gap-4">
                {/* Placeholder for Date Filter */}
                <Button variant="outline" size="sm" className="gap-2">
                    <Calendar className="w-4 h-4" />
                    <span>January 2026</span>
                </Button>
            </div>
        </header>
    );
}
