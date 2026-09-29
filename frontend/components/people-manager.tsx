"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import { ArrowDownLeft, ArrowUpRight, Pencil, Plus, Trash2, Users, X } from "lucide-react";

import { Button } from "@/components/ui/button";
import { useCurrency } from "@/components/currency-provider";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { ledgerRequest } from "@/lib/ledger-api";
import type { IOUAdjustmentDirection, IOUEvent, IOUEventType, PersonDetail, PersonSummary } from "@/lib/ledger-types";

type EventForm = {
  event_type: IOUEventType;
  amount_cad: string;
  date: string;
  adjustment_direction: IOUAdjustmentDirection;
  notes: string;
};

const selectClass = "h-10 w-full rounded-lg border bg-white px-3 text-sm outline-none focus:ring-2 focus:ring-primary";
const today = () => new Date().toISOString().slice(0, 10);
const emptyEvent = (): EventForm => ({ event_type: "lent", amount_cad: "", date: today(), adjustment_direction: "owes_user", notes: "" });
const eventLabels: Record<IOUEventType, string> = {
  borrowed: "Borrowed from them",
  lent: "Lent to them",
  repayment_received: "Repayment received",
  repayment_made: "Repayment made",
  adjustment: "Adjustment"
};

export function PeopleManager() {
  const { formatMoney } = useCurrency();
  const [people, setPeople] = useState<PersonSummary[]>([]);
  const [selected, setSelected] = useState<PersonDetail | null>(null);
  const [personName, setPersonName] = useState("");
  const [personNotes, setPersonNotes] = useState("");
  const [editingPerson, setEditingPerson] = useState(false);
  const [eventForm, setEventForm] = useState<EventForm>(emptyEvent);
  const [editingEvent, setEditingEvent] = useState<IOUEvent | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async (preferredId?: string) => {
    const summaries = await ledgerRequest<PersonSummary[]>("people");
    setPeople(summaries);
    const id = preferredId ?? summaries[0]?.id;
    if (id && summaries.some((person) => person.id === id)) {
      setSelected(await ledgerRequest<PersonDetail>(`people/${id}`));
    } else {
      setSelected(null);
    }
  }, []);

  useEffect(() => {
    void refresh().catch((reason) => setError(reason instanceof Error ? reason.message : "Unable to load people")).finally(() => setLoading(false));
  }, [refresh]);

  async function choosePerson(personId: string) {
    try { setSelected(await ledgerRequest<PersonDetail>(`people/${personId}`)); setError(null); resetEvent(); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Unable to load person"); }
  }

  async function submitPerson(event: FormEvent) {
    event.preventDefault(); setSaving(true); setError(null);
    try {
      const person = await ledgerRequest<PersonDetail>(editingPerson && selected ? `people/${selected.id}` : "people", {
        method: editingPerson ? "PATCH" : "POST",
        body: JSON.stringify({ name: personName, notes: personNotes || null })
      });
      setPersonName(""); setPersonNotes(""); setEditingPerson(false); await refresh(person.id);
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Unable to save person"); }
    finally { setSaving(false); }
  }

  function beginPersonEdit() {
    if (!selected) return;
    setPersonName(selected.name); setPersonNotes(selected.notes ?? ""); setEditingPerson(true);
  }

  function cancelPersonEdit() { setPersonName(""); setPersonNotes(""); setEditingPerson(false); }

  async function removePerson() {
    if (!selected || !window.confirm(`Delete ${selected.name} and their entire IOU history?`)) return;
    try { await ledgerRequest<void>(`people/${selected.id}`, { method: "DELETE" }); cancelPersonEdit(); resetEvent(); await refresh(); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Unable to delete person"); }
  }

  function updateEvent<K extends keyof EventForm>(key: K, value: EventForm[K]) {
    setEventForm((current) => ({ ...current, [key]: value }));
  }

  function resetEvent() { setEditingEvent(null); setEventForm(emptyEvent()); }

  function beginEventEdit(item: IOUEvent) {
    setEditingEvent(item);
    setEventForm({
      event_type: item.event_type,
      amount_cad: item.amount_cad,
      date: item.date,
      adjustment_direction: item.adjustment_direction ?? "owes_user",
      notes: item.notes ?? ""
    });
  }

  async function submitEvent(event: FormEvent) {
    event.preventDefault();
    if (!selected) return;
    setSaving(true); setError(null);
    const payload = {
      event_type: eventForm.event_type,
      amount_cad: eventForm.amount_cad,
      date: eventForm.date,
      adjustment_direction: eventForm.event_type === "adjustment" ? eventForm.adjustment_direction : null,
      notes: eventForm.notes || null
    };
    try {
      await ledgerRequest(editingEvent ? `people/${selected.id}/events/${editingEvent.id}` : `people/${selected.id}/events`, {
        method: editingEvent ? "PATCH" : "POST",
        body: JSON.stringify(payload)
      });
      resetEvent(); await refresh(selected.id);
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Unable to save IOU event"); }
    finally { setSaving(false); }
  }

  async function removeEvent(item: IOUEvent) {
    if (!selected || !window.confirm("Delete this IOU event? The outstanding balance will be recalculated.")) return;
    try { await ledgerRequest<void>(`people/${selected.id}/events/${item.id}`, { method: "DELETE" }); if (editingEvent?.id === item.id) resetEvent(); await refresh(selected.id); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Unable to delete IOU event"); }
  }

  return (
    <div className="mx-auto max-w-7xl">
      <div><p className="text-sm font-medium text-primary">Phase 9</p><h1 className="mt-1 text-3xl font-semibold tracking-tight">People and IOUs</h1><p className="mt-2 text-sm text-muted-foreground">Balances are calculated from each loan, repayment, and adjustment. Positive amounts never change account balances.</p></div>
      {error && <p className="mt-5 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</p>}

      <div className="mt-7 grid gap-6 xl:grid-cols-[340px_minmax(0,1fr)]">
        <div className="space-y-5">
          <Card><CardHeader className="flex-row items-center justify-between space-y-0"><CardTitle>{editingPerson ? "Edit person" : "Add person"}</CardTitle>{editingPerson && <button onClick={cancelPersonEdit} aria-label="Cancel editing"><X className="size-4" /></button>}</CardHeader><CardContent><form className="space-y-4" onSubmit={submitPerson}>
            <label className="block text-sm font-medium">Name<Input className="mt-1.5" value={personName} onChange={(event) => setPersonName(event.target.value)} maxLength={100} required placeholder="Alex" /></label>
            <label className="block text-sm font-medium">Notes<textarea className="mt-1.5 min-h-20 w-full rounded-lg border bg-white p-3 text-sm outline-none focus:ring-2 focus:ring-primary" value={personNotes} onChange={(event) => setPersonNotes(event.target.value)} placeholder="Optional context" /></label>
            <Button className="w-full" type="submit" disabled={saving}><Plus className="mr-2 size-4" />{saving ? "Saving…" : editingPerson ? "Save person" : "Add person"}</Button>
          </form></CardContent></Card>

          <div className="space-y-2">
            {loading && <p className="text-sm text-muted-foreground">Loading people…</p>}
            {!loading && !people.length && <Card><CardContent className="py-10 text-center"><Users className="mx-auto size-6 text-muted-foreground" /><p className="mt-3 text-sm text-muted-foreground">No people added yet.</p></CardContent></Card>}
            {people.map((person) => <button key={person.id} className={`w-full rounded-xl border p-4 text-left transition-colors ${selected?.id === person.id ? "border-primary bg-primary/5" : "bg-white hover:bg-muted/40"}`} onClick={() => void choosePerson(person.id)}><div className="flex items-start justify-between gap-3"><div><p className="font-medium">{person.name}</p><p className={`mt-1 text-xs ${person.direction === "user_owes" ? "text-red-700" : person.direction === "owed_to_user" ? "text-emerald-700" : "text-muted-foreground"}`}>{directionLabel(person)}</p></div><p className="font-semibold">{formatMoney(person.outstanding_amount_cad)}</p></div><p className="mt-3 text-xs text-muted-foreground">{person.last_activity ? `Last activity ${formatDate(person.last_activity)}` : "No activity"} · {person.event_count} event{person.event_count === 1 ? "" : "s"}</p></button>)}
          </div>
        </div>

        {!selected ? <Card><CardContent className="py-20 text-center text-sm text-muted-foreground">Select or add a person to view their IOU history.</CardContent></Card> : <div className="space-y-5">
          <Card><CardContent className="p-5"><div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-start"><div><p className="text-sm text-muted-foreground">{selected.direction === "settled" ? "Settled" : selected.direction === "owed_to_user" ? `${selected.name} owes you` : `You owe ${selected.name}`}</p><p className={`mt-1 text-3xl font-semibold ${selected.direction === "user_owes" ? "text-red-700" : selected.direction === "owed_to_user" ? "text-emerald-700" : ""}`}>{formatMoney(selected.outstanding_amount_cad)}</p>{selected.notes && <p className="mt-2 text-sm text-muted-foreground">{selected.notes}</p>}</div><div className="flex gap-1"><button className="rounded p-2 text-muted-foreground hover:bg-muted" onClick={beginPersonEdit} aria-label={`Edit ${selected.name}`}><Pencil className="size-4" /></button><button className="rounded p-2 text-red-600 hover:bg-red-50" onClick={() => void removePerson()} aria-label={`Delete ${selected.name}`}><Trash2 className="size-4" /></button></div></div></CardContent></Card>

          <Card><CardHeader className="flex-row items-center justify-between space-y-0"><CardTitle>{editingEvent ? "Edit IOU event" : "Record IOU event"}</CardTitle>{editingEvent && <button onClick={resetEvent} aria-label="Cancel event editing"><X className="size-4" /></button>}</CardHeader><CardContent><form className="grid gap-4 md:grid-cols-2" onSubmit={submitEvent}>
            <label className="block text-sm font-medium">Event<select className={`${selectClass} mt-1.5`} value={eventForm.event_type} onChange={(event) => updateEvent("event_type", event.target.value as IOUEventType)}>{Object.entries(eventLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
            <label className="block text-sm font-medium">Amount CAD<Input className="mt-1.5" type="number" min="0.01" step="0.01" value={eventForm.amount_cad} onChange={(event) => updateEvent("amount_cad", event.target.value)} required /></label>
            <label className="block text-sm font-medium">Date<Input className="mt-1.5" type="date" value={eventForm.date} onChange={(event) => updateEvent("date", event.target.value)} required /></label>
            {eventForm.event_type === "adjustment" && <label className="block text-sm font-medium">Adjustment direction<select className={`${selectClass} mt-1.5`} value={eventForm.adjustment_direction} onChange={(event) => updateEvent("adjustment_direction", event.target.value as IOUAdjustmentDirection)}><option value="owes_user">They owe you</option><option value="user_owes">You owe them</option></select></label>}
            <label className="block text-sm font-medium md:col-span-2">Notes<textarea className="mt-1.5 min-h-20 w-full rounded-lg border bg-white p-3 text-sm outline-none focus:ring-2 focus:ring-primary" value={eventForm.notes} onChange={(event) => updateEvent("notes", event.target.value)} /></label>
            <div className="md:col-span-2"><p className="mb-3 text-xs text-muted-foreground">Borrowed increases what you owe. Lent increases what they owe. Repayments reduce the corresponding debt.</p><Button type="submit" disabled={saving}>{saving ? "Saving…" : editingEvent ? "Save event" : "Record event"}</Button></div>
          </form></CardContent></Card>

          <Card><CardHeader><CardTitle>Complete history</CardTitle></CardHeader><CardContent>{selected.events.length ? <div className="divide-y">{selected.events.map((item) => <div key={item.id} className="flex gap-3 py-4 first:pt-0 last:pb-0"><span className={`grid size-9 shrink-0 place-items-center rounded-full ${Number(item.effect_cad) >= 0 ? "bg-emerald-100 text-emerald-700" : "bg-red-100 text-red-700"}`}>{Number(item.effect_cad) >= 0 ? <ArrowDownLeft className="size-4" /> : <ArrowUpRight className="size-4" />}</span><div className="min-w-0 flex-1"><div className="flex flex-wrap items-start justify-between gap-2"><div><p className="text-sm font-medium">{eventLabels[item.event_type]}</p><p className="mt-0.5 text-xs text-muted-foreground">{formatDate(item.date)}{item.notes ? ` · ${item.notes}` : ""}</p></div><div className="text-right"><p className={`text-sm font-semibold ${Number(item.effect_cad) >= 0 ? "text-emerald-700" : "text-red-700"}`}>{Number(item.effect_cad) >= 0 ? "+" : "−"}{formatMoney(Math.abs(Number(item.effect_cad)).toFixed(2))}</p><p className="mt-0.5 text-xs text-muted-foreground">Balance {signedBalance(item.running_balance_cad, formatMoney)}</p></div></div></div><div className="flex shrink-0"><button className="rounded p-2 text-muted-foreground hover:bg-muted" onClick={() => beginEventEdit(item)} aria-label="Edit event"><Pencil className="size-4" /></button><button className="rounded p-2 text-red-600 hover:bg-red-50" onClick={() => void removeEvent(item)} aria-label="Delete event"><Trash2 className="size-4" /></button></div></div>)}</div> : <p className="py-8 text-center text-sm text-muted-foreground">No IOU events for {selected.name}.</p>}</CardContent></Card>
        </div>}
      </div>
    </div>
  );
}

function directionLabel(person: PersonSummary) {
  if (person.direction === "owed_to_user") return "Owes you";
  if (person.direction === "user_owes") return "You owe";
  return "Settled";
}

function signedBalance(value: string, formatMoney: (value: string | number) => string) {
  const amount = Number(value);
  if (amount > 0) return `${formatMoney(value)} owed to you`;
  if (amount < 0) return `${formatMoney(Math.abs(amount).toFixed(2))} you owe`;
  return "settled";
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat("en-CA", { dateStyle: "medium", timeZone: "UTC" }).format(new Date(`${value}T00:00:00Z`));
}
