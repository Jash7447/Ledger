"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import { Pencil, Plus, Trash2, X } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { formatCad, ledgerRequest } from "@/lib/ledger-api";
import type { BudgetProgress, ClassificationCatalog } from "@/lib/ledger-types";

const selectClass = "h-10 w-full rounded-lg border bg-white px-3 text-sm outline-none focus:ring-2 focus:ring-primary";

function currentMonth() {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
}

export function BudgetsManager() {
  const [month, setMonth] = useState(currentMonth);
  const [budgets, setBudgets] = useState<BudgetProgress[]>([]);
  const [catalog, setCatalog] = useState<ClassificationCatalog | null>(null);
  const [target, setTarget] = useState("");
  const [amount, setAmount] = useState("");
  const [editing, setEditing] = useState<BudgetProgress | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [budgetData, catalogData] = await Promise.all([
        ledgerRequest<BudgetProgress[]>(`budgets?month=${month}`),
        ledgerRequest<ClassificationCatalog>("classifications")
      ]);
      setBudgets(budgetData); setCatalog(catalogData); setError(null);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to load budgets");
    } finally { setLoading(false); }
  }, [month]);

  useEffect(() => { void load(); }, [load]);

  function resetForm() { setEditing(null); setTarget(""); setAmount(""); }
  function beginEdit(budget: BudgetProgress) {
    setEditing(budget);
    setTarget(`${budget.scope_type}:${budget.bucket_id ?? budget.category_id}`);
    setAmount(budget.amount_cad);
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    const [scopeType, scopeId] = target.split(":");
    if (!scopeId) { setError("Select a bucket or category"); return; }
    setSaving(true); setError(null);
    const payload = {
      month,
      amount_cad: amount,
      bucket_id: scopeType === "bucket" ? scopeId : null,
      category_id: scopeType === "category" ? scopeId : null
    };
    try {
      await ledgerRequest(editing ? `budgets/${editing.id}` : "budgets", {
        method: editing ? "PATCH" : "POST", body: JSON.stringify(payload)
      });
      resetForm(); await load();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to save budget");
    } finally { setSaving(false); }
  }

  async function remove(budget: BudgetProgress) {
    if (!window.confirm(`Delete the ${budget.scope_name} budget?`)) return;
    try {
      await ledgerRequest<void>(`budgets/${budget.id}`, { method: "DELETE" });
      if (editing?.id === budget.id) resetForm();
      await load();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to delete budget");
    }
  }

  return (
    <div className="mx-auto max-w-7xl">
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
        <div><p className="text-sm font-medium text-primary">Phase 7</p><h1 className="mt-1 text-3xl font-semibold tracking-tight">Monthly budgets</h1><p className="mt-2 text-sm text-muted-foreground">Set limits for buckets or individual expense categories.</p></div>
        <label className="text-xs font-medium text-muted-foreground">Budget month<input type="month" value={month} onChange={(event) => { setMonth(event.target.value); resetForm(); }} className="mt-1 block h-10 rounded-lg border bg-white px-3 text-sm text-foreground outline-none focus:ring-2 focus:ring-primary" /></label>
      </div>
      {error && <p className="mt-5 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</p>}

      <div className="mt-7 grid gap-6 xl:grid-cols-[minmax(0,1fr)_360px]">
        <div className="grid content-start gap-4 md:grid-cols-2">
          {loading && <p className="text-sm text-muted-foreground">Loading budgets…</p>}
          {!loading && budgets.length === 0 && <Card className="md:col-span-2"><CardContent className="py-12 text-center text-sm text-muted-foreground">No budgets for this month. Create one to begin tracking progress.</CardContent></Card>}
          {budgets.map((budget) => <BudgetCard key={budget.id} budget={budget} onEdit={() => beginEdit(budget)} onDelete={() => void remove(budget)} />)}
        </div>

        <Card className="h-fit"><CardHeader className="flex-row items-center justify-between space-y-0"><CardTitle>{editing ? "Edit budget" : "Create budget"}</CardTitle>{editing && <button onClick={resetForm} aria-label="Cancel editing"><X className="size-4" /></button>}</CardHeader><CardContent><form className="space-y-4" onSubmit={submit}>
          <label className="block text-sm font-medium">Budget applies to<select className={`${selectClass} mt-1.5`} value={target} onChange={(event) => setTarget(event.target.value)} required><option value="">Select bucket or category</option><optgroup label="Buckets">{catalog?.buckets.map((bucket) => <option key={bucket.id} value={`bucket:${bucket.id}`}>{bucket.name}</option>)}</optgroup>{catalog?.buckets.map((bucket) => <optgroup key={bucket.id} label={`${bucket.name} categories`}>{bucket.categories.map((category) => <option key={category.id} value={`category:${category.id}`}>{category.name}</option>)}</optgroup>)}</select></label>
          <label className="block text-sm font-medium">Monthly limit (CAD)<Input className="mt-1.5" type="number" min="0.01" step="0.01" value={amount} onChange={(event) => setAmount(event.target.value)} placeholder="300.00" required /></label>
          <p className="text-xs leading-5 text-muted-foreground">Spending is calculated from expense transactions dated within the selected month.</p>
          <Button className="w-full" type="submit" disabled={saving}><Plus className="mr-2 size-4" />{saving ? "Saving…" : editing ? "Save changes" : "Create budget"}</Button>
        </form></CardContent></Card>
      </div>
    </div>
  );
}

function BudgetCard({ budget, onEdit, onDelete }: { budget: BudgetProgress; onEdit: () => void; onDelete: () => void }) {
  const width = Math.min(Number(budget.percentage_used), 100);
  const progressTone = budget.is_over_budget ? "bg-red-600" : Number(budget.percentage_used) >= 80 ? "bg-amber-500" : "bg-primary";
  return <Card className={budget.is_over_budget ? "border-red-200" : ""}><CardHeader className="flex-row items-start justify-between space-y-0"><div><CardTitle>{budget.scope_name}</CardTitle><p className="mt-1 text-xs capitalize text-muted-foreground">{budget.scope_type} budget</p></div><div className="flex gap-1"><button onClick={onEdit} className="rounded p-2 text-muted-foreground hover:bg-muted" aria-label={`Edit ${budget.scope_name} budget`}><Pencil className="size-4" /></button><button onClick={onDelete} className="rounded p-2 text-muted-foreground hover:bg-muted" aria-label={`Delete ${budget.scope_name} budget`}><Trash2 className="size-4" /></button></div></CardHeader><CardContent>
    <div className="flex items-end justify-between gap-3"><div><p className="text-2xl font-semibold">{formatCad(budget.spent_cad)}</p><p className="text-xs text-muted-foreground">of {formatCad(budget.amount_cad)}</p></div><p className={`text-sm font-semibold ${budget.is_over_budget ? "text-red-700" : ""}`}>{budget.percentage_used}%</p></div>
    <div className="mt-4 h-2 overflow-hidden rounded-full bg-muted"><div className={`h-full rounded-full ${progressTone}`} style={{ width: `${width}%` }} /></div>
    <div className="mt-3 flex justify-between text-xs"><span className="text-muted-foreground">Remaining</span><span className={budget.is_over_budget ? "font-medium text-red-700" : "font-medium"}>{formatCad(budget.remaining_cad)}</span></div>
    {budget.is_over_budget && <p className="mt-3 rounded-md bg-red-50 px-2.5 py-2 text-xs font-medium text-red-700">Over budget by {formatCad(String(Math.abs(Number(budget.remaining_cad))))}</p>}
  </CardContent></Card>;
}
