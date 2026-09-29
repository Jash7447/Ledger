"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { ArrowDownLeft, ArrowRight, ArrowRightLeft, ArrowUpRight, BookOpen, Clock3, PiggyBank, ReceiptText, Target, Users, Wallet } from "lucide-react";

import { SpendingByBucketChart, SpendingByCategoryChart } from "@/components/dashboard-charts";
import { useCurrency } from "@/components/currency-provider";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ledgerRequest } from "@/lib/ledger-api";
import type { Account, BudgetProgress, DashboardData, LedgerTransaction, RunwayEstimate } from "@/lib/ledger-types";

function currentMonth() {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
}

export function Dashboard() {
  const { formatMoney } = useCurrency();
  const [month, setMonth] = useState(currentMonth);
  const [data, setData] = useState<DashboardData | null>(null);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [loading, setLoading] = useState(true);
  const [runwaySaving, setRunwaySaving] = useState(false);
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
  async function updateRunway(changes: { is_enabled?: boolean; lookback_months?: number }) {
    setRunwaySaving(true);
    try { await ledgerRequest("settings/runway", { method: "PATCH", body: JSON.stringify(changes) }); await load(); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Unable to update runway settings"); }
    finally { setRunwaySaving(false); }
  }
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

      <RunwayCard runway={data.runway} saving={runwaySaving} onUpdate={updateRunway} />

      <div className="mt-6 grid gap-5 xl:grid-cols-2">
        <Card><CardHeader><CardTitle>Spending by bucket</CardTitle><p className="text-xs text-muted-foreground">Where this month&apos;s expenses went</p></CardHeader><CardContent><SpendingByBucketChart items={data.spending_by_bucket} /></CardContent></Card>
        <Card><CardHeader><CardTitle>Top spending categories</CardTitle><p className="text-xs text-muted-foreground">Up to eight categories for the selected month</p></CardHeader><CardContent><SpendingByCategoryChart items={data.spending_by_category} /></CardContent></Card>
      </div>

      <div className="mt-6 grid gap-5 xl:grid-cols-[minmax(0,1.5fr)_minmax(320px,1fr)]">
        <Card><CardHeader className="flex-row items-center justify-between space-y-0"><CardTitle>Recent transactions</CardTitle><Link href="/transactions" className="flex items-center gap-1 text-xs font-medium text-primary">View history <ArrowRight className="size-3" /></Link></CardHeader><CardContent>{data.recent_transactions.length ? <div className="divide-y">{data.recent_transactions.map((item) => <TransactionRow key={item.id} item={item} accountName={accountNames[item.account_id]} />)}</div> : <DashboardEmpty text="No transactions yet." href="/transactions" action="Add a transaction" />}</CardContent></Card>
        <div className="space-y-5">
          <Card><CardHeader className="flex-row items-center justify-between space-y-0"><CardTitle>Education spending</CardTitle><Link href="/education" className="flex items-center gap-1 text-xs font-medium text-primary">View report <ArrowRight className="size-3" /></Link></CardHeader><CardContent><div className="flex items-center gap-4"><span className="grid size-11 place-items-center rounded-full bg-blue-100 text-blue-700"><BookOpen className="size-5" /></span><div><p className="text-2xl font-semibold">{formatMoney(summary.education_spending_cad)}</p><p className="text-xs text-muted-foreground">Selected month</p></div></div></CardContent></Card>
          <Card><CardHeader className="flex-row items-center justify-between space-y-0"><CardTitle>Budget progress</CardTitle><Link href="/budgets" className="flex items-center gap-1 text-xs font-medium text-primary">Manage <ArrowRight className="size-3" /></Link></CardHeader><CardContent>{data.budget_progress.length ? <div className="space-y-4">{data.budget_progress.slice(0, 4).map((budget) => <DashboardBudget key={budget.id} budget={budget} />)}</div> : <DashboardEmpty text="No budgets for this month." href="/budgets" action="Create a budget" />}</CardContent></Card>
          <Card><CardHeader className="flex-row items-center justify-between space-y-0"><CardTitle>Money with people</CardTitle><Link href="/people" className="flex items-center gap-1 text-xs font-medium text-primary">View people <ArrowRight className="size-3" /></Link></CardHeader><CardContent><div className="grid grid-cols-2 gap-4"><div><div className="flex items-center gap-2 text-xs text-muted-foreground"><Users className="size-3.5" />Owed to you</div><p className="mt-2 text-xl font-semibold text-emerald-700">{formatMoney(summary.money_owed_to_user_cad)}</p></div><div><div className="flex items-center gap-2 text-xs text-muted-foreground"><Users className="size-3.5" />You owe</div><p className="mt-2 text-xl font-semibold text-red-700">{formatMoney(summary.money_owed_to_others_cad)}</p></div></div></CardContent></Card>
        </div>
      </div>

      <Card className="mt-6"><CardHeader><CardTitle>Recent major purchases</CardTitle></CardHeader><CardContent>{data.major_purchases.length ? <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">{data.major_purchases.map((item) => <div key={item.id} className="rounded-lg border p-4"><div className="flex items-start justify-between gap-3"><div><p className="font-medium">{item.description}</p><p className="mt-1 text-xs text-muted-foreground">{formatDate(item.date)} · {accountNames[item.account_id] ?? "Account"}</p></div><ReceiptText className="size-4 text-muted-foreground" /></div><p className="mt-4 text-lg font-semibold text-red-700">{formatMoney(item.amount_cad)}</p></div>)}</div> : <p className="py-5 text-center text-sm text-muted-foreground">No major purchases recorded.</p>}</CardContent></Card>

      <Card className="mt-6"><CardHeader className="flex-row items-center justify-between space-y-0"><CardTitle>Savings goals</CardTitle><Link href="/goals" className="flex items-center gap-1 text-xs font-medium text-primary">Manage goals <ArrowRight className="size-3" /></Link></CardHeader><CardContent>{data.goals.length ? <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">{data.goals.map((goal) => <div key={goal.id} className="rounded-lg border p-4"><div className="flex items-center justify-between gap-2"><p className="font-medium">{goal.name}</p><Target className="size-4 text-muted-foreground" /></div><p className="mt-3 text-lg font-semibold">{formatMoney(goal.current_amount_cad)} <span className="text-xs font-normal text-muted-foreground">of {formatMoney(goal.target_amount_cad)}</span></p><div className="mt-3 h-2 overflow-hidden rounded-full bg-muted"><div className={`h-full rounded-full ${goal.status === "completed" ? "bg-emerald-600" : "bg-primary"}`} style={{ width: `${Math.min(Number(goal.percentage_complete), 100)}%` }} /></div><p className="mt-2 text-xs capitalize text-muted-foreground">{goal.percentage_complete}% · {goal.status}</p></div>)}</div> : <DashboardEmpty text="No savings goals yet." href="/goals" action="Create a goal" />}</CardContent></Card>
    </div>
  );
}

function SummaryCard({ title, value, icon: Icon, tone, detail }: { title: string; value: string; icon: typeof Wallet; tone?: "positive" | "negative"; detail?: string }) {
  const { formatMoney } = useCurrency();
  const color = tone === "positive" ? "text-emerald-700" : tone === "negative" ? "text-red-700" : "text-foreground";
  return <Card><CardContent className="p-5"><div className="flex items-center justify-between"><p className="text-sm text-muted-foreground">{title}</p><Icon className="size-4 text-muted-foreground" /></div><p className={`mt-3 text-2xl font-semibold ${color}`}>{formatMoney(value)}</p>{detail && <p className="mt-1 text-xs text-muted-foreground">{detail}</p>}</CardContent></Card>;
}

function TransactionRow({ item, accountName }: { item: LedgerTransaction; accountName?: string }) {
  const { formatMoney } = useCurrency();
  const Icon = item.type === "income" ? ArrowDownLeft : item.type === "expense" ? ArrowUpRight : ArrowRightLeft;
  const sign = item.type === "income" ? "+" : item.type === "expense" ? "−" : "";
  const tone = item.type === "income" ? "text-emerald-700" : item.type === "expense" ? "text-red-700" : "text-blue-700";
  return <div className="flex items-center gap-3 py-3 first:pt-0 last:pb-0"><span className="grid size-9 shrink-0 place-items-center rounded-full bg-muted"><Icon className={`size-4 ${tone}`} /></span><div className="min-w-0 flex-1"><p className="truncate text-sm font-medium">{item.description}</p><p className="mt-0.5 text-xs text-muted-foreground">{formatDate(item.date)} · {accountName ?? "Account"}</p></div><p className={`text-sm font-semibold ${tone}`}>{sign}{formatMoney(item.amount_cad)}</p></div>;
}

function DashboardBudget({ budget }: { budget: BudgetProgress }) {
  const { formatMoney } = useCurrency();
  const width = Math.min(Number(budget.percentage_used), 100);
  return <div><div className="flex items-center justify-between gap-3 text-sm"><div><p className="font-medium">{budget.scope_name}</p><p className="text-xs text-muted-foreground">{formatMoney(budget.spent_cad)} of {formatMoney(budget.amount_cad)}</p></div><p className={budget.is_over_budget ? "font-semibold text-red-700" : "font-semibold"}>{budget.percentage_used}%</p></div><div className="mt-2 h-2 overflow-hidden rounded-full bg-muted"><div className={`h-full rounded-full ${budget.is_over_budget ? "bg-red-600" : Number(budget.percentage_used) >= 80 ? "bg-amber-500" : "bg-primary"}`} style={{ width: `${width}%` }} /></div></div>;
}

function RunwayCard({ runway, saving, onUpdate }: { runway: RunwayEstimate; saving: boolean; onUpdate: (changes: { is_enabled?: boolean; lookback_months?: number }) => Promise<void> }) {
  const { formatMoney } = useCurrency();
  return <Card className="mt-6"><CardContent className="p-5"><div className="flex flex-col justify-between gap-4 md:flex-row md:items-center"><div className="flex items-start gap-3"><span className="grid size-10 shrink-0 place-items-center rounded-full bg-cyan-100 text-cyan-700"><Clock3 className="size-5" /></span><div><div className="flex flex-wrap items-center gap-2"><p className="font-medium">Estimated financial runway</p><span className="rounded-full bg-muted px-2 py-0.5 text-[11px] text-muted-foreground">Estimate only</span></div>{!runway.is_enabled ? <p className="mt-2 text-sm text-muted-foreground">Runway estimate is disabled.</p> : runway.estimated_months ? <p className="mt-2 text-2xl font-semibold">{runway.estimated_months} months</p> : <p className="mt-2 text-sm text-muted-foreground">Not enough positive balance or spending history to estimate.</p>}<p className="mt-1 text-xs text-muted-foreground">{formatMoney(runway.available_funds_cad)} available ÷ {formatMoney(runway.average_monthly_spending_cad)} average monthly spending. This is not a prediction or guarantee.</p></div></div><div className="flex shrink-0 items-end gap-3"><label className="text-xs text-muted-foreground">History<select disabled={saving} className="mt-1 block h-9 rounded-lg border bg-white px-2 text-sm text-foreground" value={runway.lookback_months} onChange={(event) => void onUpdate({ lookback_months: Number(event.target.value) })}><option value={1}>1 month</option><option value={3}>3 months</option><option value={6}>6 months</option><option value={12}>12 months</option><option value={24}>24 months</option></select></label><button disabled={saving} onClick={() => void onUpdate({ is_enabled: !runway.is_enabled })} className="h-9 rounded-lg border bg-white px-3 text-xs font-medium hover:bg-muted disabled:opacity-50">{runway.is_enabled ? "Disable" : "Enable"}</button></div></div></CardContent></Card>;
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
