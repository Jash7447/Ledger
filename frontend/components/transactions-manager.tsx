"use client";

import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import { ArrowDownLeft, ArrowRightLeft, ArrowUpRight, Pencil, Trash2, X } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  emptyTransactionFilters,
  TransactionHistoryFilters,
  type TransactionFilters
} from "@/components/transaction-history-filters";
import { formatCad, ledgerRequest } from "@/lib/ledger-api";
import type { Account, ClassificationCatalog, LedgerTransaction, TransactionPage, TransactionType } from "@/lib/ledger-types";

type FormState = {
  type: TransactionType; account_id: string; destination_account_id: string; amount_cad: string;
  date: string; description: string; bucket_id: string; category_id: string; notes: string;
  expense_classification: "" | "fixed" | "variable"; is_major_purchase: boolean;
};

const selectClass = "h-10 w-full rounded-lg border bg-white px-3 text-sm outline-none focus:ring-2 focus:ring-primary";
const today = () => new Date().toISOString().slice(0, 10);
const emptyForm = (): FormState => ({ type: "expense", account_id: "", destination_account_id: "", amount_cad: "", date: today(), description: "", bucket_id: "", category_id: "", notes: "", expense_classification: "", is_major_purchase: false });

function historyQuery(filters: TransactionFilters, page: number) {
  const params = new URLSearchParams({
    page: String(page), page_size: filters.page_size,
    sort_by: filters.sort_by, sort_direction: filters.sort_direction
  });
  for (const key of ["search", "date_from", "date_to", "account_id", "bucket_id", "category_id", "type", "is_major_purchase"] as const) {
    if (filters[key]) params.set(key, filters[key]);
  }
  return `transactions?${params.toString()}`;
}

export function TransactionsManager() {
  const [transactions, setTransactions] = useState<LedgerTransaction[]>([]);
  const [history, setHistory] = useState({ total: 0, pages: 1, page_size: 25 });
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [catalog, setCatalog] = useState<ClassificationCatalog | null>(null);
  const [form, setForm] = useState<FormState>(emptyForm);
  const [editing, setEditing] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filterDraft, setFilterDraft] = useState<TransactionFilters>({ ...emptyTransactionFilters });
  const [filters, setFilters] = useState<TransactionFilters>({ ...emptyTransactionFilters });
  const [page, setPage] = useState(1);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [transactionData, accountData, catalogData] = await Promise.all([
        ledgerRequest<TransactionPage>(historyQuery(filters, page)),
        ledgerRequest<Account[]>("accounts?include_archived=true"),
        ledgerRequest<ClassificationCatalog>("classifications")
      ]);
      if (transactionData.page > transactionData.pages) {
        setPage(transactionData.pages);
        return;
      }
      setTransactions(transactionData.items);
      setHistory({ total: transactionData.total, pages: transactionData.pages, page_size: transactionData.page_size });
      setAccounts(accountData); setCatalog(catalogData); setError(null);
      setForm((current) => current.account_id || !accountData.length ? current : { ...current, account_id: accountData.find((item) => item.is_active)?.id ?? "" });
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to load transactions");
    } finally { setLoading(false); }
  }, [filters, page]);

  useEffect(() => { void load(); }, [load]);

  const accountNames = useMemo(() => Object.fromEntries(accounts.map((item) => [item.id, item.name])), [accounts]);
  const categoryNames = useMemo(() => {
    if (!catalog) return {};
    const categories = [...catalog.buckets.flatMap((bucket) => bucket.categories), ...catalog.income_categories, ...catalog.funding_categories];
    return Object.fromEntries(categories.map((item) => [item.id, item.name]));
  }, [catalog]);
  const bucketNames = useMemo(() => Object.fromEntries((catalog?.buckets ?? []).map((item) => [item.id, item.name])), [catalog]);
  const activeAccounts = accounts.filter((item) => item.is_active || item.id === form.account_id || item.id === form.destination_account_id);
  const selectedBucket = catalog?.buckets.find((item) => item.id === form.bucket_id);
  function update<K extends keyof FormState>(key: K, value: FormState[K]) { setForm((current) => ({ ...current, [key]: value })); }
  function changeType(type: TransactionType) { setForm((current) => ({ ...current, type, destination_account_id: "", bucket_id: "", category_id: "", expense_classification: "", is_major_purchase: false })); }
  function reset() { setEditing(null); setForm({ ...emptyForm(), account_id: accounts.find((item) => item.is_active)?.id ?? "" }); }
  function beginEdit(item: LedgerTransaction) {
    setEditing(item.id);
    setForm({ type: item.type, account_id: item.account_id, destination_account_id: item.destination_account_id ?? "", amount_cad: item.amount_cad, date: item.date, description: item.description, bucket_id: item.bucket_id ?? "", category_id: item.category_id ?? "", notes: item.notes ?? "", expense_classification: item.expense_classification ?? "", is_major_purchase: item.is_major_purchase });
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  async function submit(event: FormEvent) {
    event.preventDefault(); setSaving(true); setError(null);
    const payload = {
      type: form.type, account_id: form.account_id, amount_cad: form.amount_cad, date: form.date,
      description: form.description, notes: form.notes || null,
      destination_account_id: form.type === "transfer" ? form.destination_account_id : null,
      bucket_id: form.type === "expense" ? form.bucket_id || null : null,
      category_id: form.type === "expense" || form.type === "income" ? form.category_id || null : null,
      expense_classification: form.type === "expense" ? form.expense_classification || null : null,
      is_major_purchase: form.type === "expense" && form.is_major_purchase
    };
    try {
      await ledgerRequest(editing ? `transactions/${editing}` : "transactions", { method: editing ? "PATCH" : "POST", body: JSON.stringify(payload) });
      reset(); await load();
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Unable to save transaction"); }
    finally { setSaving(false); }
  }

  async function remove(item: LedgerTransaction) {
    if (!window.confirm(`Delete “${item.description}”? This will update account balances.`)) return;
    try { await ledgerRequest<void>(`transactions/${item.id}`, { method: "DELETE" }); if (editing === item.id) reset(); await load(); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Unable to delete transaction"); }
  }

  return (
    <div className="mx-auto max-w-7xl">
      <div><p className="text-sm font-medium text-primary">Phase 5</p><h1 className="mt-1 text-3xl font-semibold tracking-tight">Transaction history</h1><p className="mt-2 text-sm text-muted-foreground">Search, filter, sort, and inspect your complete financial record.</p></div>
      {error && <p className="mt-5 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</p>}
      <div className="mt-7 grid gap-6 xl:grid-cols-[390px_minmax(0,1fr)]">
        <Card className="h-fit"><CardHeader className="flex-row items-center justify-between space-y-0"><CardTitle>{editing ? "Edit transaction" : "New transaction"}</CardTitle>{editing && <button onClick={reset} aria-label="Cancel editing"><X className="size-4" /></button>}</CardHeader><CardContent>
          {accounts.filter((item) => item.is_active).length === 0 ? <p className="text-sm text-muted-foreground">Create an active account before adding transactions.</p> : <form className="space-y-4" onSubmit={submit}>
            <label className="block text-sm font-medium">Type<select className={`${selectClass} mt-1.5`} value={form.type} onChange={(event) => changeType(event.target.value as TransactionType)}><option value="expense">Expense</option><option value="income">Income / funding</option><option value="transfer">Transfer</option></select></label>
            <label className="block text-sm font-medium">{form.type === "transfer" ? "From account" : "Account"}<select className={`${selectClass} mt-1.5`} value={form.account_id} onChange={(event) => update("account_id", event.target.value)} required><option value="">Select account</option>{activeAccounts.map((item) => <option key={item.id} value={item.id}>{item.name}{!item.is_active ? " (archived)" : ""}</option>)}</select></label>
            {form.type === "transfer" && <label className="block text-sm font-medium">To account<select className={`${selectClass} mt-1.5`} value={form.destination_account_id} onChange={(event) => update("destination_account_id", event.target.value)} required><option value="">Select account</option>{activeAccounts.filter((item) => item.id !== form.account_id).map((item) => <option key={item.id} value={item.id}>{item.name}{!item.is_active ? " (archived)" : ""}</option>)}</select></label>}
            <div className="grid grid-cols-2 gap-3"><label className="block text-sm font-medium">Amount (CAD)<Input className="mt-1.5" type="number" min="0.01" step="0.01" value={form.amount_cad} onChange={(event) => update("amount_cad", event.target.value)} required /></label><label className="block text-sm font-medium">Date<Input className="mt-1.5" type="date" value={form.date} onChange={(event) => update("date", event.target.value)} required /></label></div>
            <label className="block text-sm font-medium">Description<Input className="mt-1.5" value={form.description} onChange={(event) => update("description", event.target.value)} required maxLength={255} /></label>
            {form.type === "expense" && <><label className="block text-sm font-medium">Bucket<select className={`${selectClass} mt-1.5`} value={form.bucket_id} onChange={(event) => { update("bucket_id", event.target.value); update("category_id", ""); }}><option value="">Uncategorized</option>{catalog?.buckets.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label><label className="block text-sm font-medium">Category<select className={`${selectClass} mt-1.5`} value={form.category_id} onChange={(event) => update("category_id", event.target.value)} disabled={!form.bucket_id}><option value="">Uncategorized</option>{selectedBucket?.categories.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label><label className="block text-sm font-medium">Expense classification<select className={`${selectClass} mt-1.5`} value={form.expense_classification} onChange={(event) => update("expense_classification", event.target.value as FormState["expense_classification"])}><option value="">Not set</option><option value="fixed">Fixed</option><option value="variable">Variable</option></select></label><label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={form.is_major_purchase} onChange={(event) => update("is_major_purchase", event.target.checked)} /> Major purchase</label></>}
            {form.type === "income" && <label className="block text-sm font-medium">Income / funding category<select className={`${selectClass} mt-1.5`} value={form.category_id} onChange={(event) => update("category_id", event.target.value)}><option value="">Uncategorized</option><optgroup label="Earned income">{catalog?.income_categories.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</optgroup><optgroup label="External funding">{catalog?.funding_categories.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</optgroup></select></label>}
            <label className="block text-sm font-medium">Notes<textarea className="mt-1.5 min-h-20 w-full rounded-lg border bg-white p-3 text-sm outline-none focus:ring-2 focus:ring-primary" value={form.notes} onChange={(event) => update("notes", event.target.value)} /></label>
            <Button className="w-full" type="submit" disabled={saving}>{saving ? "Saving…" : editing ? "Save changes" : "Add transaction"}</Button>
          </form>}
        </CardContent></Card>

        <div className="space-y-3">
          <TransactionHistoryFilters
            value={filterDraft}
            accounts={accounts}
            catalog={catalog}
            onChange={setFilterDraft}
            onApply={() => { setPage(1); setFilters({ ...filterDraft }); }}
            onClear={() => { const cleared = { ...emptyTransactionFilters }; setFilterDraft(cleared); setFilters(cleared); setPage(1); }}
          />
          {!loading && <div className="flex items-center justify-between text-sm text-muted-foreground"><span>{history.total} {history.total === 1 ? "transaction" : "transactions"}</span>{history.total > 0 && <span>Page {page} of {history.pages}</span>}</div>}
          {loading && <p className="text-sm text-muted-foreground">Loading transactions…</p>}
          {!loading && !transactions.length && <Card><CardContent className="py-12 text-center text-sm text-muted-foreground">No transactions match these filters.</CardContent></Card>}
          {transactions.map((item) => {
            const Icon = item.type === "income" ? ArrowDownLeft : item.type === "expense" ? ArrowUpRight : ArrowRightLeft;
            const open = expanded === item.id;
            return <Card key={item.id}><CardContent className="p-0"><button className="flex w-full items-center gap-4 p-5 text-left" onClick={() => setExpanded(open ? null : item.id)}>
              <span className={`grid size-10 shrink-0 place-items-center rounded-full ${item.type === "income" ? "bg-emerald-100 text-emerald-700" : item.type === "expense" ? "bg-red-100 text-red-700" : "bg-blue-100 text-blue-700"}`}><Icon className="size-5" /></span>
              <span className="min-w-0 flex-1"><span className="block truncate font-medium">{item.description}</span><span className="mt-1 block text-xs text-muted-foreground">{new Date(`${item.date}T00:00:00`).toLocaleDateString("en-CA", { dateStyle: "medium" })} · {accountNames[item.account_id] ?? "Unknown account"}{item.type === "transfer" && ` → ${accountNames[item.destination_account_id ?? ""] ?? "Unknown account"}`}</span></span>
              <span className={`font-semibold ${item.type === "income" ? "text-emerald-700" : item.type === "expense" ? "text-red-700" : ""}`}>{item.type === "income" ? "+" : item.type === "expense" ? "−" : ""}{formatCad(item.amount_cad)}</span>
            </button>{open && <div className="border-t bg-muted/30 px-5 py-4 text-sm"><div className="grid gap-2 sm:grid-cols-2"><p><span className="text-muted-foreground">Type:</span> <span className="capitalize">{item.type}</span></p><p><span className="text-muted-foreground">Classification:</span> {item.expense_classification ?? "—"}</p><p><span className="text-muted-foreground">Bucket:</span> {item.bucket_id ? bucketNames[item.bucket_id] : "—"}</p><p><span className="text-muted-foreground">Category:</span> {item.category_id ? categoryNames[item.category_id] : "—"}</p><p><span className="text-muted-foreground">Major purchase:</span> {item.is_major_purchase ? "Yes" : "No"}</p><p><span className="text-muted-foreground">Notes:</span> {item.notes || "—"}</p></div><div className="mt-4 flex gap-2"><Button className="h-9" onClick={() => beginEdit(item)}><Pencil className="mr-2 size-4" />Edit</Button><Button className="h-9 bg-red-600" onClick={() => void remove(item)}><Trash2 className="mr-2 size-4" />Delete</Button></div></div>}</CardContent></Card>;
          })}
          {!loading && history.pages > 1 && <div className="flex items-center justify-end gap-2 pt-2"><Button className="border bg-white text-foreground hover:bg-muted" disabled={page <= 1} onClick={() => setPage((current) => current - 1)}>Previous</Button><Button disabled={page >= history.pages} onClick={() => setPage((current) => current + 1)}>Next</Button></div>}
        </div>
      </div>
    </div>
  );
}
