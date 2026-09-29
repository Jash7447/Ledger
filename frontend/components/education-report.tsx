"use client";

import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { ArrowRight, BookOpen, CalendarDays, GraduationCap, ReceiptText } from "lucide-react";

import { SpendingByCategoryChart } from "@/components/dashboard-charts";
import { useCurrency } from "@/components/currency-provider";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { ledgerRequest } from "@/lib/ledger-api";
import type { Account, EducationReport } from "@/lib/ledger-types";

function defaultDates() {
  const now = new Date();
  const end = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`;
  return { date_from: `${now.getFullYear()}-01-01`, date_to: end };
}

export function EducationReportView() {
  const { formatMoney } = useCurrency();
  const [draft, setDraft] = useState(defaultDates);
  const [range, setRange] = useState(defaultDates);
  const [report, setReport] = useState<EducationReport | null>(null);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [reportData, accountData] = await Promise.all([
        ledgerRequest<EducationReport>(`education?date_from=${range.date_from}&date_to=${range.date_to}`),
        ledgerRequest<Account[]>("accounts?include_archived=true")
      ]);
      setReport(reportData); setAccounts(accountData); setError(null);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to load education report");
    } finally { setLoading(false); }
  }, [range]);

  useEffect(() => { void load(); }, [load]);
  const accountNames = useMemo(() => Object.fromEntries(accounts.map((item) => [item.id, item.name])), [accounts]);
  const chartItems = report?.spending_by_category.map((item) => ({ id: item.category_id, name: item.category_name, amount_cad: item.amount_cad })) ?? [];
  const topCategory = report?.spending_by_category[0];
  function apply(event: FormEvent) { event.preventDefault(); setRange({ ...draft }); }

  return (
    <div className="mx-auto max-w-7xl">
      <div className="flex flex-col justify-between gap-4 lg:flex-row lg:items-end"><div><p className="text-sm font-medium text-primary">Phase 8</p><h1 className="mt-1 text-3xl font-semibold tracking-tight">Education report</h1><p className="mt-2 text-sm text-muted-foreground">Tuition, fees, books, software, exams, and other education expenses.</p></div><form className="flex flex-wrap items-end gap-2" onSubmit={apply}><label className="text-xs font-medium text-muted-foreground">From<Input className="mt-1" type="date" value={draft.date_from} onChange={(event) => setDraft((current) => ({ ...current, date_from: event.target.value }))} required /></label><label className="text-xs font-medium text-muted-foreground">To<Input className="mt-1" type="date" min={draft.date_from} value={draft.date_to} onChange={(event) => setDraft((current) => ({ ...current, date_to: event.target.value }))} required /></label><Button type="submit">Apply range</Button></form></div>
      {error && <p className="mt-5 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</p>}
      {loading && !report && <div className="mt-8 animate-pulse space-y-5"><div className="grid gap-4 md:grid-cols-3">{Array.from({ length: 3 }).map((_, index) => <div className="h-28 rounded-xl bg-muted" key={index} />)}</div><div className="h-80 rounded-xl bg-muted" /></div>}
      {report && <>
        <div className="mt-7 grid gap-4 md:grid-cols-3"><MetricCard icon={GraduationCap} label="Education spending" value={formatMoney(report.total_spent_cad)} /><MetricCard icon={ReceiptText} label="Transactions" value={String(report.transaction_count)} /><MetricCard icon={BookOpen} label="Top category" value={topCategory?.category_name ?? "No spending"} detail={topCategory ? formatMoney(topCategory.amount_cad) : undefined} /></div>
        <div className="mt-6 grid gap-5 xl:grid-cols-[minmax(0,1fr)_minmax(0,1.2fr)]">
          <Card><CardHeader><CardTitle>Spending by education category</CardTitle><p className="text-xs text-muted-foreground">For {formatDate(report.date_from)} through {formatDate(report.date_to)}</p></CardHeader><CardContent><SpendingByCategoryChart items={chartItems} /></CardContent></Card>
          <Card><CardHeader className="flex-row items-center justify-between space-y-0"><CardTitle>Education expenses</CardTitle><Link href="/transactions" className="flex items-center gap-1 text-xs font-medium text-primary">All transactions <ArrowRight className="size-3" /></Link></CardHeader><CardContent>{report.transactions.length ? <div className="divide-y">{report.transactions.map((item) => <div key={item.id} className="flex items-center gap-3 py-3 first:pt-0 last:pb-0"><span className="grid size-9 shrink-0 place-items-center rounded-full bg-blue-100 text-blue-700"><CalendarDays className="size-4" /></span><div className="min-w-0 flex-1"><p className="truncate text-sm font-medium">{item.description}</p><p className="mt-0.5 text-xs text-muted-foreground">{formatDate(item.date)} · {accountNames[item.account_id] ?? "Account"}</p></div><p className="text-sm font-semibold text-red-700">−{formatMoney(item.amount_cad)}</p></div>)}</div> : <div className="py-10 text-center text-sm text-muted-foreground"><p>No education expenses in this range.</p><Link href="/transactions" className="mt-2 inline-block font-medium text-primary">Record an expense</Link></div>}</CardContent></Card>
        </div>
      </>}
    </div>
  );
}

function MetricCard({ icon: Icon, label, value, detail }: { icon: typeof GraduationCap; label: string; value: string; detail?: string }) {
  return <Card><CardContent className="p-5"><div className="flex items-center justify-between"><p className="text-sm text-muted-foreground">{label}</p><Icon className="size-4 text-muted-foreground" /></div><p className="mt-3 text-2xl font-semibold">{value}</p>{detail && <p className="mt-1 text-xs text-muted-foreground">{detail}</p>}</CardContent></Card>;
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat("en-CA", { dateStyle: "medium", timeZone: "UTC" }).format(new Date(`${value}T00:00:00Z`));
}
