"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import { Archive, Pencil, Plus, X } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { formatCad, ledgerRequest } from "@/lib/ledger-api";
import type { Account, AccountType } from "@/lib/ledger-types";

const accountTypes: { value: AccountType; label: string }[] = [
  { value: "chequing", label: "Chequing" },
  { value: "savings", label: "Savings" },
  { value: "credit_card", label: "Credit Card" },
  { value: "cash", label: "Cash" },
  { value: "other", label: "Other" }
];

const selectClass = "h-10 w-full rounded-lg border bg-white px-3 text-sm outline-none focus:ring-2 focus:ring-primary";

export function AccountsManager() {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [name, setName] = useState("");
  const [type, setType] = useState<AccountType>("chequing");
  const [editing, setEditing] = useState<Account | null>(null);
  const [showArchived, setShowArchived] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setAccounts(await ledgerRequest<Account[]>(`accounts?include_archived=${showArchived}`));
      setError(null);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to load accounts");
    } finally {
      setLoading(false);
    }
  }, [showArchived]);

  useEffect(() => { void load(); }, [load]);

  function beginEdit(account: Account) {
    setEditing(account);
    setName(account.name);
    setType(account.type);
  }

  function resetForm() {
    setEditing(null);
    setName("");
    setType("chequing");
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError(null);
    try {
      await ledgerRequest(editing ? `accounts/${editing.id}` : "accounts", {
        method: editing ? "PATCH" : "POST",
        body: JSON.stringify({ name, type, ...(editing ? {} : { currency: "CAD" }) })
      });
      resetForm();
      await load();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to save account");
    } finally {
      setSaving(false);
    }
  }

  async function archive(account: Account) {
    if (!window.confirm(`Archive ${account.name}? Existing transactions will be preserved.`)) return;
    try {
      await ledgerRequest<void>(`accounts/${account.id}/archive`, { method: "POST" });
      await load();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to archive account");
    }
  }

  return (
    <div className="mx-auto max-w-6xl">
      <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-end">
        <div><p className="text-sm font-medium text-primary">Phase 4</p><h1 className="mt-1 text-3xl font-semibold tracking-tight">Accounts</h1><p className="mt-2 text-sm text-muted-foreground">Balances are calculated from transactions in CAD.</p></div>
        <label className="flex items-center gap-2 text-sm text-muted-foreground"><input type="checkbox" checked={showArchived} onChange={(event) => setShowArchived(event.target.checked)} /> Show archived</label>
      </div>

      {error && <p className="mt-5 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</p>}
      <div className="mt-7 grid gap-6 lg:grid-cols-[minmax(0,1fr)_340px]">
        <div className="grid content-start gap-4 sm:grid-cols-2">
          {loading && <p className="text-sm text-muted-foreground">Loading accounts…</p>}
          {!loading && accounts.length === 0 && <Card className="sm:col-span-2"><CardContent className="py-10 text-center text-sm text-muted-foreground">No accounts yet. Add your first account to begin.</CardContent></Card>}
          {accounts.map((account) => (
            <Card key={account.id} className={!account.is_active ? "opacity-60" : ""}>
              <CardHeader className="flex-row items-start justify-between space-y-0">
                <div><CardTitle>{account.name}</CardTitle><p className="mt-1 text-xs capitalize text-muted-foreground">{account.type.replace("_", " ")}{!account.is_active && " · Archived"}</p></div>
                {account.is_active && <div className="flex gap-1"><button onClick={() => beginEdit(account)} className="rounded p-2 text-muted-foreground hover:bg-muted" aria-label={`Edit ${account.name}`}><Pencil className="size-4" /></button><button onClick={() => void archive(account)} className="rounded p-2 text-muted-foreground hover:bg-muted" aria-label={`Archive ${account.name}`}><Archive className="size-4" /></button></div>}
              </CardHeader>
              <CardContent><p className={`text-2xl font-semibold ${Number(account.balance_cad) < 0 ? "text-red-600" : ""}`}>{formatCad(account.balance_cad)}</p><p className="mt-1 text-xs text-muted-foreground">Derived balance</p></CardContent>
            </Card>
          ))}
        </div>

        <Card className="h-fit">
          <CardHeader className="flex-row items-center justify-between space-y-0"><CardTitle>{editing ? "Edit account" : "Add account"}</CardTitle>{editing && <button onClick={resetForm} aria-label="Cancel editing"><X className="size-4" /></button>}</CardHeader>
          <CardContent><form className="space-y-4" onSubmit={submit}>
            <label className="block text-sm font-medium">Name<Input className="mt-1.5" value={name} onChange={(event) => setName(event.target.value)} placeholder="Daily chequing" required maxLength={100} /></label>
            <label className="block text-sm font-medium">Type<select className={`${selectClass} mt-1.5`} value={type} onChange={(event) => setType(event.target.value as AccountType)}>{accountTypes.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}</select></label>
            <p className="text-xs text-muted-foreground">Currency: CAD (source of truth)</p>
            <Button className="w-full" type="submit" disabled={saving}><Plus className="mr-2 size-4" />{saving ? "Saving…" : editing ? "Save changes" : "Add account"}</Button>
          </form></CardContent>
        </Card>
      </div>
    </div>
  );
}
