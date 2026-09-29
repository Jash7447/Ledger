"use client";

import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { useCurrency } from "@/components/currency-provider";
import type { MonthlyAnalyticsItem, SpendingBreakdownItem } from "@/lib/ledger-types";

function axisMoney(value: number, currency: string, rate: string) {
  const converted = currency === "INR" ? value * Number(rate) : value;
  return `${currency === "INR" ? "₹" : "$"}${Intl.NumberFormat("en", { notation: "compact", maximumFractionDigits: 1 }).format(converted)}`;
}

function AnalyticsTooltip({ active, payload, label }: { active?: boolean; payload?: Array<{ dataKey?: string; name?: string; value?: number; color?: string }>; label?: string }) {
  const { formatMoney } = useCurrency();
  if (!active || !payload?.length) return null;
  return <div className="rounded-lg border bg-white px-3 py-2 text-xs shadow-lg"><p className="mb-1 font-medium">{label}</p>{payload.map((item) => <p key={item.dataKey} style={{ color: item.color }}>{item.name}: {formatMoney(item.value ?? 0)}</p>)}</div>;
}

export function MonthlyComparisonChart({ items }: { items: MonthlyAnalyticsItem[] }) {
  const { settings } = useCurrency();
  const data = items.map((item) => ({ month: item.month, Income: Number(item.income_cad), Expenses: Number(item.expenses_cad), Savings: Number(item.savings_cad) }));
  if (!data.some((item) => item.Income || item.Expenses)) return <ChartEmpty />;
  return <div className="h-80"><ResponsiveContainer width="100%" height="100%"><BarChart data={data} accessibilityLayer><CartesianGrid strokeDasharray="3 3" vertical={false} /><XAxis dataKey="month" tick={{ fontSize: 11 }} /><YAxis tickFormatter={(value) => axisMoney(Number(value), settings.display_currency, settings.cad_to_inr_rate)} tick={{ fontSize: 11 }} /><Tooltip content={<AnalyticsTooltip />} /><Legend /><Bar dataKey="Income" fill="#0f8a65" radius={[4, 4, 0, 0]} /><Bar dataKey="Expenses" fill="#dc2626" radius={[4, 4, 0, 0]} /></BarChart></ResponsiveContainer></div>;
}

export function ClassificationChart({ items }: { items: SpendingBreakdownItem[] }) {
  const { settings } = useCurrency();
  const data = items.map((item) => ({ name: item.name, Spending: Number(item.amount_cad) }));
  if (!data.length) return <ChartEmpty />;
  return <div className="h-64"><ResponsiveContainer width="100%" height="100%"><BarChart data={data} layout="vertical" accessibilityLayer><CartesianGrid strokeDasharray="3 3" horizontal={false} /><XAxis type="number" tickFormatter={(value) => axisMoney(Number(value), settings.display_currency, settings.cad_to_inr_rate)} tick={{ fontSize: 11 }} /><YAxis type="category" dataKey="name" width={90} tick={{ fontSize: 11 }} /><Tooltip content={<AnalyticsTooltip />} /><Bar dataKey="Spending" fill="#7c3aed" radius={[0, 4, 4, 0]} /></BarChart></ResponsiveContainer></div>;
}

function ChartEmpty() {
  return <div className="grid h-64 place-items-center rounded-lg bg-muted/40 text-sm text-muted-foreground">No activity in this period.</div>;
}
