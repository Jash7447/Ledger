"use client";

import { Activity, Gauge, LayoutDashboard, Wallet } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { SignOutButton } from "@/components/sign-out-button";
import type { CurrentUser } from "@/lib/auth";

const navigation = [
  { label: "Overview", href: "/", icon: LayoutDashboard },
  { label: "Accounts", href: "/accounts", icon: Wallet },
  { label: "Transactions", href: "/transactions", icon: Activity },
  { label: "Budgets", href: "/budgets", icon: Gauge }
];

export function AppShell({ children, user }: { children: React.ReactNode; user: CurrentUser }) {
  const pathname = usePathname();
  return (
    <main className="min-h-screen lg:flex">
      <aside className="flex border-b bg-white px-6 py-5 lg:min-h-screen lg:w-64 lg:flex-col lg:border-b-0 lg:border-r">
        <div className="w-full">
          <div className="flex items-center gap-3">
            <div className="grid size-9 place-items-center rounded-lg bg-primary text-sm font-bold text-primary-foreground">L</div>
            <span className="text-lg font-semibold tracking-tight">Ledger</span>
          </div>
          <nav className="mt-10 grid gap-2" aria-label="Primary navigation">
            {navigation.map(({ label, href, icon: Icon }) => (
              <Link key={href} href={href} className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm ${pathname === href ? "bg-muted font-medium" : "text-muted-foreground hover:bg-muted/60"}`}>
                <Icon className="size-4" aria-hidden="true" />
                {label}
              </Link>
            ))}
          </nav>
        </div>
        <div className="mt-auto hidden border-t pt-4 lg:block">
          <div className="mb-2 px-3">
            <p className="truncate text-sm font-medium">{user.display_name}</p>
            <p className="truncate text-xs text-muted-foreground">{user.email}</p>
          </div>
          <SignOutButton />
        </div>
      </aside>
      <section className="flex-1 p-6 lg:p-10">{children}</section>
    </main>
  );
}
