"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { ArrowDownLeft, ArrowRight, ArrowRightLeft, ArrowUpRight, BookOpen, PiggyBank, ReceiptText, Users, Wallet } from "lucide-react";

import { SpendingByBucketChart, SpendingByCategoryChart } from "@/components/dashboard-charts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatCad, ledgerRequest } from "@/lib/ledger-api";
import type { Account, BudgetProgress, DashboardData, LedgerTransaction } from "@/lib/ledger-types";

function currentMonth() {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
}

export function Dashboard() {
  const [month, setMonth] = useState(currentMonth);
  const [data, setData] = useState<DashboardData | null>(null);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [dashboard, accountData] = await Promise.all([
        ledgerRequest<DashboardData>(`dashboard?month=${month}`),
        ledgerRequest<Account[]>("accounts?include_archived=true")
      ]);
      setData(dashboard); setAccounts(accountData); setError(null);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to load dashboard");
    } finally { setLoading(false); }
  }, [month]);

  useEffect(() => { void load(); }, [load]);
  const accountNames = useMemo(() => Object.fromEntries(accounts.map((item) => [item.id, item.name])), [accounts]);
  const periodLabel = data ? new Intl.DateTimeFormat("en-CA", { month: "long", year: "numeric", timeZone: "UTC" }).format(new Date(`${data.period_start}T00:00:00Z`)) : "Selected month";

  if (loading && !data) return <DashboardLoading />;
  if (error && !data) return <div className="mx-auto max-w-6xl rounded-lg border border-red-200 bg-red-50 p-5 text-sm text-red-700">{error}<button className="ml-2 underline" onClick={() => void load()}>Try again</button></div>;
  if (!data) return null;

  const summary = data.summary;
  const savingsNegative = Number(summary.monthly_savings_cad) < 0;
  return (
    <div className="mx-auto max-w-7xl">
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
        <div><p className="text-sm font-medium text-primary">{periodLabel}</p><h1 className="mt-1 text-3xl font-semibold tracking-tight">Financial overview</h1><p className="mt-2 text-sm text-muted-foreground">A current view of balances, spending, and recent activity.</p></div>
        <label className="text-xs font-medium text-muted-foreground">Reporting month<input type="month" value={month} onChange={(event) => setMonth(event.target.value)} className="mt-1 block h-10 rounded-lg border bg-white px-3 text-sm text-foreground outline-none focus:ring-2 focus:ring-primary" /></label>
      </div>
      {error && <p className="mt-5 rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">Showing the last loaded data. Refresh failed: {error}</p>}

      <div className="mt-7 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <SummaryCard title="Current balance" value={summary.current_balance_cad} icon={Wallet} detail="Across active accounts" />
        <SummaryCard title="Monthly income" value={summary.monthly_income_cad} icon={ArrowDownLeft} tone="positive" />
        <SummaryCard title="Monthly expenses" value={summary.monthly_expenses_cad} icon={ArrowUpRight} tone="negative" />
        <SummaryCard title="Monthly savings" value={summary.monthly_savings_cad} icon={PiggyBank} tone={savingsNegative ? "negative" : "positive"} detail="Income minus expenses" />
      </div>

      <div className="mt-6 grid gap-5 xl:grid-cols-2">
        <Card><CardHeader><CardTitle>Spending by bucket</CardTitle><p className="text-xs text-muted-foreground">Where this month&apos;s expenses went</p></CardHeader><CardContent><SpendingByBucketChart items={data.spending_by_bucket} /></CardContent></Card>
        <Card><CardHeader><CardTitle>Top spending categories</CardTitle><p className="text-xs text-muted-foreground">Up to eight categories for the selected month</p></CardHeader><CardContent><SpendingByCategoryChart items={data.spending_by_category} /></CardContent></Card>
      </div>

      <div className="mt-6 grid gap-5 xl:grid-cols-[minmax(0,1.5fr)_minmax(320px,1fr)]">
        <Card><CardHeader className="flex-row items-center justify-between space-y-0"><CardTitle>Recent transactions</CardTitle><Link href="/transactions" className="flex items-center gap-1 text-xs font-medium text-primary">View history <ArrowRight className="size-3" /></Link></CardHeader><CardContent>{data.recent_transactions.length ? <div className="divide-y">{data.recent_transactions.map((item) => <TransactionRow key={item.id} item={item} accountName={accountNames[item.account_id]} />)}</div> : <DashboardEmpty text="No transactions yet." href="/transactions" action="Add a transaction" />}</CardContent></Card>
        <div className="space-y-5">
          <Card><CardHeader><CardTitle>Education spending</CardTitle></CardHeader><CardContent><div className="flex items-center gap-4"><span className="grid size-11 place-items-center rounded-full bg-blue-100 text-blue-700"><BookOpen className="size-5" /></span><div><p className="text-2xl font-semibold">{formatCad(summary.education_spending_cad)}</p><p className="text-xs text-muted-foreground">Selected month</p></div></div></CardContent></Card>
          <Card><CardHeader className="flex-row items-center justify-between space-y-0"><CardTitle>Budget progress</CardTitle><Link href="/budgets" className="flex items-center gap-1 text-xs font-medium text-primary">Manage <ArrowRight className="size-3" /></Link></CardHeader><CardContent>{data.budget_progress.length ? <div className="space-y-4">{data.budget_progress.slice(0, 4).map((budget) => <DashboardBudget key={budget.id} budget={budget} />)}</div> : <DashboardEmpty text="No budgets for this month." href="/budgets" action="Create a budget" />}</CardContent></Card>
          <Card><CardHeader><CardTitle>Money with people</CardTitle></CardHeader><CardContent><UnavailableState icon={Users} text="No IOU tracking yet" detail="Amounts owed will appear after People and IOUs are set up." /></CardContent></Card>
        </div>
      </div>

      <Card className="mt-6"><CardHeader><CardTitle>Recent major purchases</CardTitle></CardHeader><CardContent>{data.major_purchases.length ? <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">{data.major_purchases.map((item) => <div key={item.id} className="rounded-lg border p-4"><div className="flex items-start justify-between gap-3"><div><p className="font-medium">{item.description}</p><p className="mt-1 text-xs text-muted-foreground">{formatDate(item.date)} · {accountNames[item.account_id] ?? "Account"}</p></div><ReceiptText className="size-4 text-muted-foreground" /></div><p className="mt-4 text-lg font-semibold text-red-700">{formatCad(item.amount_cad)}</p></div>)}</div> : <p className="py-5 text-center text-sm text-muted-foreground">No major purchases recorded.</p>}</CardContent></Card>
    </div>
  );
}

function SummaryCard({ title, value, icon: Icon, tone, detail }: { title: string; value: string; icon: typeof Wallet; tone?: "positive" | "negative"; detail?: string }) {
  const color = tone === "positive" ? "text-emerald-700" : tone === "negative" ? "text-red-700" : "text-foreground";
  return <Card><CardContent className="p-5"><div className="flex items-center justify-between"><p className="text-sm text-muted-foreground">{title}</p><Icon className="size-4 text-muted-foreground" /></div><p className={`mt-3 text-2xl font-semibold ${color}`}>{formatCad(value)}</p>{detail && <p className="mt-1 text-xs text-muted-foreground">{detail}</p>}</CardContent></Card>;
}

function TransactionRow({ item, accountName }: { item: LedgerTransaction; accountName?: string }) {
  const Icon = item.type === "income" ? ArrowDownLeft : item.type === "expense" ? ArrowUpRight : ArrowRightLeft;
  const sign = item.type === "income" ? "+" : item.type === "expense" ? "−" : "";
  const tone = item.type === "income" ? "text-emerald-700" : item.type === "expense" ? "text-red-700" : "text-blue-700";
  return <div className="flex items-center gap-3 py-3 first:pt-0 last:pb-0"><span className="grid size-9 shrink-0 place-items-center rounded-full bg-muted"><Icon className={`size-4 ${tone}`} /></span><div className="min-w-0 flex-1"><p className="truncate text-sm font-medium">{item.description}</p><p className="mt-0.5 text-xs text-muted-foreground">{formatDate(item.date)} · {accountName ?? "Account"}</p></div><p className={`text-sm font-semibold ${tone}`}>{sign}{formatCad(item.amount_cad)}</p></div>;
}

function DashboardBudget({ budget }: { budget: BudgetProgress }) {
  const width = Math.min(Number(budget.percentage_used), 100);
  return <div><div className="flex items-center justify-between gap-3 text-sm"><div><p className="font-medium">{budget.scope_name}</p><p className="text-xs text-muted-foreground">{formatCad(budget.spent_cad)} of {formatCad(budget.amount_cad)}</p></div><p className={budget.is_over_budget ? "font-semibold text-red-700" : "font-semibold"}>{budget.percentage_used}%</p></div><div className="mt-2 h-2 overflow-hidden rounded-full bg-muted"><div className={`h-full rounded-full ${budget.is_over_budget ? "bg-red-600" : Number(budget.percentage_used) >= 80 ? "bg-amber-500" : "bg-primary"}`} style={{ width: `${width}%` }} /></div></div>;
}

function UnavailableState({ icon: Icon, text, detail }: { icon: typeof Wallet; text: string; detail: string }) {
  return <div className="flex gap-3"><span className="grid size-10 shrink-0 place-items-center rounded-full bg-muted text-muted-foreground"><Icon className="size-4" /></span><div><p className="text-sm font-medium">{text}</p><p className="mt-1 text-xs leading-5 text-muted-foreground">{detail}</p></div></div>;
}

function DashboardEmpty({ text, href, action }: { text: string; href: string; action: string }) {
  return <div className="py-8 text-center text-sm text-muted-foreground"><p>{text}</p><Link href={href} className="mt-2 inline-block font-medium text-primary">{action}</Link></div>;
}

function DashboardLoading() {
  return <div className="mx-auto max-w-7xl animate-pulse"><div className="h-8 w-64 rounded bg-muted" /><div className="mt-3 h-4 w-96 max-w-full rounded bg-muted" /><div className="mt-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">{Array.from({ length: 4 }).map((_, index) => <div key={index} className="h-28 rounded-xl bg-muted" />)}</div><div className="mt-6 grid gap-5 xl:grid-cols-2"><div className="h-80 rounded-xl bg-muted" /><div className="h-80 rounded-xl bg-muted" /></div></div>;
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat("en-CA", { month: "short", day: "numeric", timeZone: "UTC" }).format(new Date(`${value}T00:00:00Z`));
}
