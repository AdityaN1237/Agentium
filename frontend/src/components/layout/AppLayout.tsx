'use client';

import { Sidebar } from "@/components/layout/Sidebar";
import { usePathname } from "next/navigation";
import { ReactNode } from "react";

export function AppLayout({ children }: { children: ReactNode }) {
    const pathname = usePathname();
    const isAuthPage = ['/login', '/signup'].includes(pathname);

    if (isAuthPage) {
        return <main className="w-full min-h-screen">{children}</main>;
    }

    return (
        <div className="flex flex-col lg:flex-row min-h-screen">
            <Sidebar />
            <main className="flex-1 overflow-x-hidden relative pt-16 lg:pt-0">
                {children}
            </main>
        </div>
    );
}
