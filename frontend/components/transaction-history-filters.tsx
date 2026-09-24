"use client";

import { FormEvent } from "react";
import { Search, SlidersHorizontal, X } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import type { Account, ClassificationCatalog, TransactionType } from "@/lib/ledger-types";

export type TransactionFilters = {
  search: string;
  date_from: string;
  date_to: string;
  account_id: string;
  bucket_id: string;
  category_id: string;
  type: "" | TransactionType;
  is_major_purchase: "" | "true" | "false";
  sort_by: "date" | "amount" | "description" | "created_at";
  sort_direction: "asc" | "desc";
  page_size: string;
};

export const emptyTransactionFilters: TransactionFilters = {
  search: "", date_from: "", date_to: "", account_id: "", bucket_id: "",
  category_id: "", type: "", is_major_purchase: "", sort_by: "date",
  sort_direction: "desc", page_size: "25"
};

const selectClass = "h-10 w-full rounded-lg border bg-white px-3 text-sm outline-none focus:ring-2 focus:ring-primary";

type Props = {
  value: TransactionFilters;
  accounts: Account[];
  catalog: ClassificationCatalog | null;
  onChange: (value: TransactionFilters) => void;
  onApply: () => void;
  onClear: () => void;
};

export function TransactionHistoryFilters({ value, accounts, catalog, onChange, onApply, onClear }: Props) {
  const allCategories = [
    ...(catalog?.buckets.flatMap((bucket) => bucket.categories) ?? []),
    ...(catalog?.income_categories ?? []),
    ...(catalog?.funding_categories ?? [])
  ];
  const visibleCategories = value.bucket_id
    ? catalog?.buckets.find((bucket) => bucket.id === value.bucket_id)?.categories ?? []
    : allCategories;
  function set<K extends keyof TransactionFilters>(key: K, next: TransactionFilters[K]) {
    onChange({ ...value, [key]: next });
  }
  function submit(event: FormEvent) { event.preventDefault(); onApply(); }

  return (
    <Card>
      <CardContent className="p-4">
        <form onSubmit={submit}>
          <div className="flex items-center gap-2 text-sm font-medium"><SlidersHorizontal className="size-4" />History filters</div>
          <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
            <label className="relative md:col-span-2 xl:col-span-4"><span className="sr-only">Search transactions</span><Search className="absolute left-3 top-3 size-4 text-muted-foreground" /><Input className="pl-9" value={value.search} onChange={(event) => set("search", event.target.value)} placeholder="Search descriptions or notes" maxLength={100} /></label>
            <label className="text-xs font-medium text-muted-foreground">From date<Input className="mt-1" type="date" value={value.date_from} onChange={(event) => set("date_from", event.target.value)} /></label>
            <label className="text-xs font-medium text-muted-foreground">To date<Input className="mt-1" type="date" value={value.date_to} onChange={(event) => set("date_to", event.target.value)} /></label>
            <label className="text-xs font-medium text-muted-foreground">Account<select className={`${selectClass} mt-1`} value={value.account_id} onChange={(event) => set("account_id", event.target.value)}><option value="">All accounts</option>{accounts.map((item) => <option key={item.id} value={item.id}>{item.name}{!item.is_active ? " (archived)" : ""}</option>)}</select></label>
            <label className="text-xs font-medium text-muted-foreground">Type<select className={`${selectClass} mt-1`} value={value.type} onChange={(event) => set("type", event.target.value as TransactionFilters["type"])}><option value="">All types</option><option value="expense">Expense</option><option value="income">Income</option><option value="transfer">Transfer</option></select></label>
            <label className="text-xs font-medium text-muted-foreground">Bucket<select className={`${selectClass} mt-1`} value={value.bucket_id} onChange={(event) => onChange({ ...value, bucket_id: event.target.value, category_id: "" })}><option value="">All buckets</option>{catalog?.buckets.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label>
            <label className="text-xs font-medium text-muted-foreground">Category<select className={`${selectClass} mt-1`} value={value.category_id} onChange={(event) => set("category_id", event.target.value)}><option value="">All categories</option>{visibleCategories.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label>
            <label className="text-xs font-medium text-muted-foreground">Major purchase<select className={`${selectClass} mt-1`} value={value.is_major_purchase} onChange={(event) => set("is_major_purchase", event.target.value as TransactionFilters["is_major_purchase"])}><option value="">All transactions</option><option value="true">Major purchases</option><option value="false">Not major</option></select></label>
            <label className="text-xs font-medium text-muted-foreground">Sort<select className={`${selectClass} mt-1`} value={`${value.sort_by}:${value.sort_direction}`} onChange={(event) => { const [sort_by, sort_direction] = event.target.value.split(":") as [TransactionFilters["sort_by"], TransactionFilters["sort_direction"]]; onChange({ ...value, sort_by, sort_direction }); }}><option value="date:desc">Newest date</option><option value="date:asc">Oldest date</option><option value="amount:desc">Highest amount</option><option value="amount:asc">Lowest amount</option><option value="description:asc">Description A–Z</option><option value="description:desc">Description Z–A</option><option value="created_at:desc">Recently added</option></select></label>
            <label className="text-xs font-medium text-muted-foreground">Per page<select className={`${selectClass} mt-1`} value={value.page_size} onChange={(event) => set("page_size", event.target.value)}><option value="10">10</option><option value="25">25</option><option value="50">50</option><option value="100">100</option></select></label>
          </div>
          <div className="mt-4 flex justify-end gap-2"><Button type="button" className="border bg-white text-foreground hover:bg-muted" onClick={onClear}><X className="mr-2 size-4" />Clear</Button><Button type="submit"><Search className="mr-2 size-4" />Apply filters</Button></div>
        </form>
      </CardContent>
    </Card>
  );
}
