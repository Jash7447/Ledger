"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";

import { useCurrency } from "@/components/currency-provider";
import type { SpendingBreakdownItem } from "@/lib/ledger-types";

const colors = ["#0f8a65", "#2563eb", "#7c3aed", "#ea580c", "#db2777", "#0891b2", "#64748b"];

function chartData(items: SpendingBreakdownItem[]) {
  return items.map((item) => ({ name: item.name, amount: Number(item.amount_cad) }));
}

function MoneyTooltip({ active, payload, label }: { active?: boolean; payload?: Array<{ value?: number; name?: string; payload?: { name?: string } }>; label?: string }) {
  const { formatMoney } = useCurrency();
  if (!active || !payload?.length) return null;
  const name = label || payload[0].payload?.name || payload[0].name;
  return <div className="rounded-lg border bg-white px-3 py-2 text-xs shadow-lg"><p className="font-medium">{name}</p><p className="mt-1 text-muted-foreground">{formatMoney(String(payload[0].value ?? 0))}</p></div>;
}

export function SpendingByBucketChart({ items }: { items: SpendingBreakdownItem[] }) {
  const data = chartData(items);
  if (!data.length) return <ChartEmptyState />;
  return (
    <div className="h-64" aria-label="Monthly spending by bucket chart">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart accessibilityLayer>
          <Pie data={data} dataKey="amount" nameKey="name" innerRadius={55} outerRadius={90} paddingAngle={2}>
            {data.map((item, index) => <Cell key={item.name} fill={colors[index % colors.length]} />)}
          </Pie>
          <Tooltip content={<MoneyTooltip />} />
        </PieChart>
      </ResponsiveContainer>
      <div className="-mt-3 flex flex-wrap justify-center gap-x-4 gap-y-1 text-xs text-muted-foreground">{data.map((item, index) => <span key={item.name} className="flex items-center gap-1.5"><span className="size-2 rounded-full" style={{ backgroundColor: colors[index % colors.length] }} />{item.name}</span>)}</div>
    </div>
  );
}

export function SpendingByCategoryChart({ items }: { items: SpendingBreakdownItem[] }) {
  const { settings } = useCurrency();
  const data = chartData(items.slice(0, 8));
  if (!data.length) return <ChartEmptyState />;
  return (
    <div className="h-72" aria-label="Monthly spending by category chart">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} layout="vertical" margin={{ left: 10, right: 16 }} accessibilityLayer>
          <CartesianGrid strokeDasharray="3 3" horizontal={false} />
          <XAxis type="number" tickFormatter={(value) => settings.display_currency === "INR" ? `₹${Math.round(Number(value) * Number(settings.cad_to_inr_rate))}` : `$${value}`} tick={{ fontSize: 11 }} />
          <YAxis type="category" dataKey="name" width={90} tick={{ fontSize: 11 }} />
          <Tooltip content={<MoneyTooltip />} />
          <Bar dataKey="amount" fill="#0f8a65" radius={[0, 5, 5, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

function ChartEmptyState() {
  return <div className="grid h-64 place-items-center rounded-lg bg-muted/40 text-sm text-muted-foreground">No expenses in this period.</div>;
}
