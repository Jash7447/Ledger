"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import { CalendarDays, Pencil, Plus, Target, Trash2, X } from "lucide-react";

import { useCurrency } from "@/components/currency-provider";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { ledgerRequest } from "@/lib/ledger-api";
import type { Goal, GoalStatus } from "@/lib/ledger-types";

type GoalForm = { name: string; target_amount_cad: string; current_amount_cad: string; target_date: string; status: GoalStatus };
const emptyForm = (): GoalForm => ({ name: "", target_amount_cad: "", current_amount_cad: "0.00", target_date: "", status: "active" });
const selectClass = "h-10 w-full rounded-lg border bg-white px-3 text-sm outline-none focus:ring-2 focus:ring-primary";

export function GoalsManager() {
  const { formatMoney } = useCurrency();
  const [goals, setGoals] = useState<Goal[]>([]);
  const [form, setForm] = useState<GoalForm>(emptyForm);
  const [editing, setEditing] = useState<Goal | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try { setGoals(await ledgerRequest<Goal[]>("goals")); setError(null); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Unable to load goals"); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => { void load(); }, [load]);
  function update<K extends keyof GoalForm>(key: K, value: GoalForm[K]) { setForm((current) => ({ ...current, [key]: value })); }
  function reset() { setEditing(null); setForm(emptyForm()); }
  function beginEdit(goal: Goal) { setEditing(goal); setForm({ name: goal.name, target_amount_cad: goal.target_amount_cad, current_amount_cad: goal.current_amount_cad, target_date: goal.target_date ?? "", status: goal.status }); }

  async function submit(event: FormEvent) {
    event.preventDefault(); setSaving(true); setError(null);
    try {
      await ledgerRequest(editing ? `goals/${editing.id}` : "goals", { method: editing ? "PATCH" : "POST", body: JSON.stringify({ ...form, target_date: form.target_date || null }) });
      reset(); await load();
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Unable to save goal"); }
    finally { setSaving(false); }
  }

  async function remove(goal: Goal) {
    if (!window.confirm(`Delete the ${goal.name} goal?`)) return;
    try { await ledgerRequest<void>(`goals/${goal.id}`, { method: "DELETE" }); if (editing?.id === goal.id) reset(); await load(); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Unable to delete goal"); }
  }

  return <div className="mx-auto max-w-7xl"><div><p className="text-sm font-medium text-primary">Phase 12</p><h1 className="mt-1 text-3xl font-semibold tracking-tight">Savings goals</h1><p className="mt-2 text-sm text-muted-foreground">Track progress toward important purchases and savings targets. Progress is entered manually and does not alter account balances.</p></div>
    {error && <p className="mt-5 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</p>}
    <div className="mt-7 grid gap-6 xl:grid-cols-[minmax(0,1fr)_380px]"><div className="grid content-start gap-4 md:grid-cols-2">{loading && <p className="text-sm text-muted-foreground">Loading goals…</p>}{!loading && !goals.length && <Card className="md:col-span-2"><CardContent className="py-12 text-center"><Target className="mx-auto size-7 text-muted-foreground" /><p className="mt-3 text-sm text-muted-foreground">No savings goals yet.</p></CardContent></Card>}{goals.map((goal) => { const width = Math.min(Number(goal.percentage_complete), 100); return <Card key={goal.id} className={goal.status === "cancelled" ? "opacity-60" : ""}><CardHeader className="flex-row items-start justify-between space-y-0"><div><CardTitle>{goal.name}</CardTitle><p className="mt-1 text-xs capitalize text-muted-foreground">{goal.status}</p></div><div className="flex"><button className="rounded p-2 text-muted-foreground hover:bg-muted" onClick={() => beginEdit(goal)} aria-label={`Edit ${goal.name}`}><Pencil className="size-4" /></button><button className="rounded p-2 text-red-600 hover:bg-red-50" onClick={() => void remove(goal)} aria-label={`Delete ${goal.name}`}><Trash2 className="size-4" /></button></div></CardHeader><CardContent><div className="flex items-end justify-between gap-3"><div><p className="text-2xl font-semibold">{formatMoney(goal.current_amount_cad)}</p><p className="text-xs text-muted-foreground">of {formatMoney(goal.target_amount_cad)}</p></div><p className="text-sm font-semibold">{goal.percentage_complete}%</p></div><div className="mt-4 h-2 overflow-hidden rounded-full bg-muted"><div className={`h-full rounded-full ${goal.status === "completed" ? "bg-emerald-600" : "bg-primary"}`} style={{ width: `${width}%` }} /></div><div className="mt-3 flex justify-between text-xs"><span className="text-muted-foreground">Remaining {formatMoney(goal.remaining_amount_cad)}</span>{goal.target_date && <span className="flex items-center gap-1 text-muted-foreground"><CalendarDays className="size-3" />{formatDate(goal.target_date)}</span>}</div></CardContent></Card>; })}</div>
      <Card className="h-fit"><CardHeader className="flex-row items-center justify-between space-y-0"><CardTitle>{editing ? "Edit goal" : "Create goal"}</CardTitle>{editing && <button onClick={reset} aria-label="Cancel editing"><X className="size-4" /></button>}</CardHeader><CardContent><form className="space-y-4" onSubmit={submit}><label className="block text-sm font-medium">Name<Input className="mt-1.5" value={form.name} onChange={(event) => update("name", event.target.value)} required maxLength={100} placeholder="New Laptop" /></label><div className="grid grid-cols-2 gap-3"><label className="block text-sm font-medium">Target CAD<Input className="mt-1.5" type="number" min="0.01" step="0.01" value={form.target_amount_cad} onChange={(event) => update("target_amount_cad", event.target.value)} required /></label><label className="block text-sm font-medium">Saved CAD<Input className="mt-1.5" type="number" min="0" step="0.01" value={form.current_amount_cad} onChange={(event) => update("current_amount_cad", event.target.value)} required /></label></div><label className="block text-sm font-medium">Target date<Input className="mt-1.5" type="date" value={form.target_date} onChange={(event) => update("target_date", event.target.value)} /></label><label className="block text-sm font-medium">Status<select className={`${selectClass} mt-1.5`} value={form.status} onChange={(event) => update("status", event.target.value as GoalStatus)}><option value="active">Active</option><option value="paused">Paused</option><option value="cancelled">Cancelled</option></select></label><p className="text-xs text-muted-foreground">Goals at or above 100% are marked completed automatically.</p><Button className="w-full" disabled={saving}><Plus className="mr-2 size-4" />{saving ? "Saving…" : editing ? "Save changes" : "Create goal"}</Button></form></CardContent></Card>
    </div>
  </div>;
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat("en-CA", { dateStyle: "medium", timeZone: "UTC" }).format(new Date(`${value}T00:00:00Z`));
}
