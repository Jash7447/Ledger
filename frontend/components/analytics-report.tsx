"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import { ArrowDownLeft, ArrowUpRight, BookOpen, PiggyBank, ReceiptText } from "lucide-react";

import { ClassificationChart, MonthlyComparisonChart } from "@/components/analytics-charts";
import { SpendingByBucketChart, SpendingByCategoryChart } from "@/components/dashboard-charts";
import { useCurrency } from "@/components/currency-provider";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { ledgerRequest } from "@/lib/ledger-api";
import type { AnalyticsData } from "@/lib/ledger-types";

function defaultDates() {
  const now = new Date();
  const date_to = now.toISOString().slice(0, 10);
  return { date_from: `${now.getFullYear()}-01-01`, date_to };
}

export function AnalyticsReport() {
  const { formatMoney } = useCurrency();
  const [draft, setDraft] = useState(defaultDates);
  const [range, setRange] = useState(defaultDates);
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try { setData(await ledgerRequest<AnalyticsData>(`analytics?date_from=${range.date_from}&date_to=${range.date_to}`)); setError(null); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Unable to load analytics"); }
    finally { setLoading(false); }
  }, [range]);
  useEffect(() => { void load(); }, [load]);
  function apply(event: FormEvent) { event.preventDefault(); setRange({ ...draft }); }

  return <div className="mx-auto max-w-7xl"><div className="flex flex-col justify-between gap-4 lg:flex-row lg:items-end"><div><p className="text-sm font-medium text-primary">Phase 11</p><h1 className="mt-1 text-3xl font-semibold tracking-tight">Analytics</h1><p className="mt-2 text-sm text-muted-foreground">Historical income, spending, savings, and classification trends.</p></div><form className="flex flex-wrap items-end gap-2" onSubmit={apply}><label className="text-xs font-medium text-muted-foreground">From<Input className="mt-1" type="date" value={draft.date_from} onChange={(event) => setDraft((current) => ({ ...current, date_from: event.target.value }))} required /></label><label className="text-xs font-medium text-muted-foreground">To<Input className="mt-1" type="date" min={draft.date_from} value={draft.date_to} onChange={(event) => setDraft((current) => ({ ...current, date_to: event.target.value }))} required /></label><Button type="submit">Apply range</Button></form></div>
    {error && <p className="mt-5 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</p>}
    {loading && !data && <div className="mt-8 h-80 animate-pulse rounded-xl bg-muted" />}
    {data && <><div className="mt-7 grid gap-4 sm:grid-cols-2 xl:grid-cols-5"><Metric label="Income" value={formatMoney(data.summary.income_cad)} icon={ArrowDownLeft} tone="positive" /><Metric label="Expenses" value={formatMoney(data.summary.expenses_cad)} icon={ArrowUpRight} tone="negative" /><Metric label="Savings" value={formatMoney(data.summary.savings_cad)} icon={PiggyBank} tone={Number(data.summary.savings_cad) < 0 ? "negative" : "positive"} /><Metric label="Education" value={formatMoney(data.summary.education_spending_cad)} icon={BookOpen} /><Metric label="Major purchases" value={formatMoney(data.summary.major_purchase_spending_cad)} icon={ReceiptText} /></div>
      <Card className="mt-6"><CardHeader><CardTitle>Monthly income vs expenses</CardTitle><p className="text-xs text-muted-foreground">Transfers are excluded from both totals.</p></CardHeader><CardContent><MonthlyComparisonChart items={data.monthly_trend} /></CardContent></Card>
      <div className="mt-6 grid gap-5 xl:grid-cols-2"><Card><CardHeader><CardTitle>Spending by bucket</CardTitle></CardHeader><CardContent><SpendingByBucketChart items={data.spending_by_bucket} /></CardContent></Card><Card><CardHeader><CardTitle>Spending by category</CardTitle></CardHeader><CardContent><SpendingByCategoryChart items={data.spending_by_category} /></CardContent></Card></div>
      <div className="mt-6 grid gap-5 xl:grid-cols-2"><Card><CardHeader><CardTitle>Fixed vs variable expenses</CardTitle></CardHeader><CardContent><ClassificationChart items={data.fixed_vs_variable} /></CardContent></Card><Card><CardHeader><CardTitle>Major purchases</CardTitle></CardHeader><CardContent>{data.major_purchases.length ? <div className="divide-y">{data.major_purchases.map((item) => <div className="flex items-center justify-between gap-3 py-3 first:pt-0 last:pb-0" key={item.id}><div><p className="text-sm font-medium">{item.description}</p><p className="text-xs text-muted-foreground">{formatDate(item.date)}</p></div><p className="font-semibold text-red-700">{formatMoney(item.amount_cad)}</p></div>)}</div> : <p className="py-10 text-center text-sm text-muted-foreground">No major purchases in this period.</p>}</CardContent></Card></div>
    </>}
  </div>;
}

function Metric({ label, value, icon: Icon, tone }: { label: string; value: string; icon: typeof PiggyBank; tone?: "positive" | "negative" }) {
  return <Card><CardContent className="p-5"><div className="flex items-center justify-between"><p className="text-sm text-muted-foreground">{label}</p><Icon className="size-4 text-muted-foreground" /></div><p className={`mt-3 text-xl font-semibold ${tone === "positive" ? "text-emerald-700" : tone === "negative" ? "text-red-700" : ""}`}>{value}</p></CardContent></Card>;
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat("en-CA", { dateStyle: "medium", timeZone: "UTC" }).format(new Date(`${value}T00:00:00Z`));
}
