"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import { CalendarClock, Pause, Pencil, Play, Plus, Trash2, X } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useCurrency } from "@/components/currency-provider";
import { ledgerRequest } from "@/lib/ledger-api";
import type { Account, ClassificationCatalog, RecurringDefinition, RecurringFrequency } from "@/lib/ledger-types";

type RecurringForm = {
  account_id: string; category_id: string; description: string; expected_amount_cad: string;
  frequency: RecurringFrequency; start_date: string; end_date: string; notes: string; is_active: boolean;
};

const selectClass = "h-10 w-full rounded-lg border bg-white px-3 text-sm outline-none focus:ring-2 focus:ring-primary";
const today = () => new Date().toISOString().slice(0, 10);
const emptyForm = (): RecurringForm => ({ account_id: "", category_id: "", description: "", expected_amount_cad: "", frequency: "monthly", start_date: today(), end_date: "", notes: "", is_active: true });

export function RecurringManager() {
  const { formatMoney } = useCurrency();
  const [items, setItems] = useState<RecurringDefinition[]>([]);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [catalog, setCatalog] = useState<ClassificationCatalog | null>(null);
  const [form, setForm] = useState<RecurringForm>(emptyForm);
  const [editing, setEditing] = useState<RecurringDefinition | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [definitions, accountData, catalogData] = await Promise.all([
        ledgerRequest<RecurringDefinition[]>("recurring"),
        ledgerRequest<Account[]>("accounts?include_archived=true"),
        ledgerRequest<ClassificationCatalog>("classifications")
      ]);
      setItems(definitions); setAccounts(accountData); setCatalog(catalogData); setError(null);
      setForm((current) => current.account_id ? current : { ...current, account_id: accountData.find((item) => item.is_active)?.id ?? "" });
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to load recurring expenses");
    } finally { setLoading(false); }
  }, []);

  useEffect(() => { void load(); }, [load]);

  function update<K extends keyof RecurringForm>(key: K, value: RecurringForm[K]) { setForm((current) => ({ ...current, [key]: value })); }
  function resetForm() { setEditing(null); setForm({ ...emptyForm(), account_id: accounts.find((item) => item.is_active)?.id ?? "" }); }
  function beginEdit(item: RecurringDefinition) {
    setEditing(item);
    setForm({ account_id: item.account_id, category_id: item.category_id, description: item.description, expected_amount_cad: item.expected_amount_cad, frequency: item.frequency, start_date: item.start_date, end_date: item.end_date ?? "", notes: item.notes ?? "", is_active: item.is_active });
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  async function submit(event: FormEvent) {
    event.preventDefault(); setSaving(true); setError(null);
    try {
      await ledgerRequest(editing ? `recurring/${editing.id}` : "recurring", {
        method: editing ? "PATCH" : "POST",
        body: JSON.stringify({ ...form, end_date: form.end_date || null, notes: form.notes || null })
      });
      resetForm(); await load();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to save recurring expense");
    } finally { setSaving(false); }
  }

  async function toggle(item: RecurringDefinition) {
    try { await ledgerRequest(`recurring/${item.id}`, { method: "PATCH", body: JSON.stringify({ is_active: !item.is_active }) }); await load(); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Unable to update recurring expense"); }
  }
  async function remove(item: RecurringDefinition) {
    if (!window.confirm(`Delete “${item.description}”?`)) return;
    try { await ledgerRequest<void>(`recurring/${item.id}`, { method: "DELETE" }); if (editing?.id === item.id) resetForm(); await load(); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Unable to delete recurring expense"); }
  }

  const availableAccounts = accounts.filter((item) => item.is_active || item.id === form.account_id);
  return (
    <div className="mx-auto max-w-7xl">
      <div><p className="text-sm font-medium text-primary">Phase 8</p><h1 className="mt-1 text-3xl font-semibold tracking-tight">Recurring expenses</h1><p className="mt-2 text-sm text-muted-foreground">Expected obligations only. These definitions never change balances or create completed transactions.</p></div>
      {error && <p className="mt-5 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</p>}
      <div className="mt-7 grid gap-6 xl:grid-cols-[390px_minmax(0,1fr)]">
        <Card className="h-fit"><CardHeader className="flex-row items-center justify-between space-y-0"><CardTitle>{editing ? "Edit recurring expense" : "Add recurring expense"}</CardTitle>{editing && <button onClick={resetForm} aria-label="Cancel editing"><X className="size-4" /></button>}</CardHeader><CardContent>
          {!accounts.some((item) => item.is_active) && !editing ? <p className="text-sm text-muted-foreground">Create an active account before adding a recurring expense.</p> : <form className="space-y-4" onSubmit={submit}>
            <label className="block text-sm font-medium">Description<Input className="mt-1.5" value={form.description} onChange={(event) => update("description", event.target.value)} placeholder="Monthly rent" required maxLength={255} /></label>
            <label className="block text-sm font-medium">Account<select className={`${selectClass} mt-1.5`} value={form.account_id} onChange={(event) => update("account_id", event.target.value)} required><option value="">Select account</option>{availableAccounts.map((item) => <option key={item.id} value={item.id}>{item.name}{!item.is_active ? " (archived)" : ""}</option>)}</select></label>
            <label className="block text-sm font-medium">Expense category<select className={`${selectClass} mt-1.5`} value={form.category_id} onChange={(event) => update("category_id", event.target.value)} required><option value="">Select category</option>{catalog?.buckets.map((bucket) => <optgroup key={bucket.id} label={bucket.name}>{bucket.categories.map((category) => <option key={category.id} value={category.id}>{category.name}</option>)}</optgroup>)}</select></label>
            <div className="grid grid-cols-2 gap-3"><label className="block text-sm font-medium">Expected CAD<Input className="mt-1.5" type="number" min="0.01" step="0.01" value={form.expected_amount_cad} onChange={(event) => update("expected_amount_cad", event.target.value)} required /></label><label className="block text-sm font-medium">Frequency<select className={`${selectClass} mt-1.5`} value={form.frequency} onChange={(event) => update("frequency", event.target.value as RecurringFrequency)}><option value="weekly">Weekly</option><option value="biweekly">Every 2 weeks</option><option value="monthly">Monthly</option><option value="quarterly">Quarterly</option><option value="yearly">Yearly</option></select></label></div>
            <div className="grid grid-cols-2 gap-3"><label className="block text-sm font-medium">Start date<Input className="mt-1.5" type="date" value={form.start_date} onChange={(event) => update("start_date", event.target.value)} required /></label><label className="block text-sm font-medium">End date<Input className="mt-1.5" type="date" min={form.start_date} value={form.end_date} onChange={(event) => update("end_date", event.target.value)} /></label></div>
            <label className="block text-sm font-medium">Notes<textarea className="mt-1.5 min-h-20 w-full rounded-lg border bg-white p-3 text-sm outline-none focus:ring-2 focus:ring-primary" value={form.notes} onChange={(event) => update("notes", event.target.value)} /></label>
            <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={form.is_active} onChange={(event) => update("is_active", event.target.checked)} /> Active expectation</label>
            <Button className="w-full" type="submit" disabled={saving}><Plus className="mr-2 size-4" />{saving ? "Saving…" : editing ? "Save changes" : "Add recurring expense"}</Button>
          </form>}
        </CardContent></Card>

        <div className="space-y-3">
          {loading && <p className="text-sm text-muted-foreground">Loading recurring expenses…</p>}
          {!loading && !items.length && <Card><CardContent className="py-12 text-center text-sm text-muted-foreground">No recurring expenses defined.</CardContent></Card>}
          {items.map((item) => <Card key={item.id} className={!item.is_active ? "opacity-65" : ""}><CardContent className="p-5"><div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-start"><div className="flex gap-3"><span className="grid size-10 shrink-0 place-items-center rounded-full bg-violet-100 text-violet-700"><CalendarClock className="size-5" /></span><div><div className="flex flex-wrap items-center gap-2"><p className="font-medium">{item.description}</p><span className={`rounded-full px-2 py-0.5 text-[11px] font-medium ${item.is_active ? "bg-emerald-100 text-emerald-700" : "bg-muted text-muted-foreground"}`}>{item.is_active ? "Active" : "Inactive"}</span></div><p className="mt-1 text-xs text-muted-foreground">{item.account_name} · {item.bucket_name} / {item.category_name}</p><p className="mt-2 text-sm"><span className="font-semibold">{formatMoney(item.expected_amount_cad)}</span> <span className="capitalize text-muted-foreground">· {item.frequency}</span></p>{item.next_occurrence_date && <p className="mt-1 text-xs text-muted-foreground">Next expected: {formatDate(item.next_occurrence_date)}</p>}{item.notes && <p className="mt-2 text-xs text-muted-foreground">{item.notes}</p>}</div></div><div className="flex gap-1"><button onClick={() => void toggle(item)} className="rounded p-2 text-muted-foreground hover:bg-muted" aria-label={item.is_active ? `Pause ${item.description}` : `Activate ${item.description}`}>{item.is_active ? <Pause className="size-4" /> : <Play className="size-4" />}</button><button onClick={() => beginEdit(item)} className="rounded p-2 text-muted-foreground hover:bg-muted" aria-label={`Edit ${item.description}`}><Pencil className="size-4" /></button><button onClick={() => void remove(item)} className="rounded p-2 text-muted-foreground hover:bg-muted" aria-label={`Delete ${item.description}`}><Trash2 className="size-4" /></button></div></div></CardContent></Card>)}
        </div>
      </div>
    </div>
  );
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat("en-CA", { dateStyle: "medium", timeZone: "UTC" }).format(new Date(`${value}T00:00:00Z`));
}
