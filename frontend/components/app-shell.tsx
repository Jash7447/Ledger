"use client";

import { FormEvent, useEffect, useState } from "react";
import { Activity, ChartNoAxesCombined, Gauge, GraduationCap, LayoutDashboard, Repeat2, Target, Users, Wallet } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { SignOutButton } from "@/components/sign-out-button";
import { useCurrency } from "@/components/currency-provider";
import { Input } from "@/components/ui/input";
import type { CurrentUser } from "@/lib/auth";

const navigation = [
  { label: "Overview", href: "/", icon: LayoutDashboard },
  { label: "Accounts", href: "/accounts", icon: Wallet },
  { label: "Transactions", href: "/transactions", icon: Activity },
  { label: "Budgets", href: "/budgets", icon: Gauge },
  { label: "Recurring", href: "/recurring", icon: Repeat2 },
  { label: "Education", href: "/education", icon: GraduationCap },
  { label: "People", href: "/people", icon: Users },
  { label: "Analytics", href: "/analytics", icon: ChartNoAxesCombined },
  { label: "Goals", href: "/goals", icon: Target }
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
          <CurrencyControls />
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

function CurrencyControls() {
  const { settings, loading, saving, error, toggleCurrency, updateSettings } = useCurrency();
  const [rate, setRate] = useState(settings.cad_to_inr_rate);
  useEffect(() => setRate(settings.cad_to_inr_rate), [settings.cad_to_inr_rate]);

  async function saveRate(event: FormEvent) {
    event.preventDefault();
    await updateSettings({ cad_to_inr_rate: rate }).catch(() => undefined);
  }

  return <div className="mt-7 rounded-lg border bg-muted/30 p-3"><div className="flex items-center justify-between gap-2"><div><p className="text-xs font-medium">Display currency</p><p className="text-[11px] text-muted-foreground">Stored in CAD</p></div><button type="button" disabled={loading || saving} onClick={() => void toggleCurrency().catch(() => undefined)} className="rounded-md border bg-white px-2.5 py-1 text-xs font-semibold hover:bg-muted disabled:opacity-50">{settings.display_currency}</button></div><form className="mt-3" onSubmit={saveRate}><label className="text-[11px] text-muted-foreground">1 CAD in INR<div className="mt-1 flex gap-1.5"><Input className="h-8 text-xs" type="number" min="0.0001" step="0.0001" value={rate} onChange={(event) => setRate(event.target.value)} required /><button disabled={saving} className="rounded-md bg-primary px-2 text-[11px] font-medium text-primary-foreground disabled:opacity-50">Save</button></div></label></form>{error && <p className="mt-2 text-[11px] text-red-700">{error}</p>}</div>;
}
