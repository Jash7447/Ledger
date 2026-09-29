"use client";

import { FormEvent, useEffect, useState } from "react";
import { CheckCircle2, MessageCircleQuestion, Send, Sparkles } from "lucide-react";

import { useCurrency } from "@/components/currency-provider";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { ledgerRequest } from "@/lib/ledger-api";
import type { Account, ClassificationCatalog, NaturalLanguageQueryResponse, NaturalLanguageTransactionProposal } from "@/lib/ledger-types";

const selectClass = "h-10 w-full rounded-lg border bg-white px-3 text-sm outline-none focus:ring-2 focus:ring-primary";

export function NaturalLanguageWorkspace() {
  const { formatMoney } = useCurrency();
  const [text, setText] = useState("");
  const [proposal, setProposal] = useState<NaturalLanguageTransactionProposal | null>(null);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [catalog, setCatalog] = useState<ClassificationCatalog | null>(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void Promise.all([
      ledgerRequest<Account[]>("accounts?include_archived=false"),
      ledgerRequest<ClassificationCatalog>("classifications")
    ]).then(([accountData, catalogData]) => { setAccounts(accountData); setCatalog(catalogData); }).catch((reason) => setError(reason instanceof Error ? reason.message : "Unable to load entry options"));
  }, []);

  async function propose(event: FormEvent) {
    event.preventDefault(); setLoading(true); setError(null); setMessage(null);
    try { setProposal(await ledgerRequest<NaturalLanguageTransactionProposal>("natural-language/transactions/propose", { method: "POST", body: JSON.stringify({ text }) })); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Unable to interpret transaction"); }
    finally { setLoading(false); }
  }

  function update<K extends keyof NaturalLanguageTransactionProposal>(key: K, value: NaturalLanguageTransactionProposal[K]) {
    setProposal((current) => {
      if (!current) return current;
      const next = { ...current, [key]: value };
      return {
        ...next,
        ready_to_confirm: Boolean(next.type && next.amount_cad && next.account_id)
      };
    });
  }

  async function confirm() {
    if (!proposal?.type || !proposal.amount_cad || !proposal.account_id) return;
    setLoading(true); setError(null);
    try {
      await ledgerRequest("natural-language/transactions/confirm", {
        method: "POST",
        body: JSON.stringify({
          source_text: proposal.source_text,
          transaction: {
            account_id: proposal.account_id,
            type: proposal.type,
            amount_cad: proposal.amount_cad,
            date: proposal.date,
            description: proposal.description,
            bucket_id: proposal.type === "expense" ? proposal.bucket_id : null,
            category_id: proposal.category_id,
            is_major_purchase: proposal.type === "expense" && proposal.is_major_purchase
          }
        })
      });
      setMessage(`Recorded ${proposal.description} for ${formatMoney(proposal.amount_cad)}.`);
      setProposal(null); setText("");
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Unable to confirm transaction"); }
    finally { setLoading(false); }
  }

  const expenseCategories = catalog?.buckets.flatMap((bucket) => bucket.categories.map((category) => ({ ...category, bucketName: bucket.name }))) ?? [];
  const incomeCategories = [...(catalog?.income_categories ?? []), ...(catalog?.funding_categories ?? [])];
  return <div className="mx-auto max-w-5xl"><div><p className="text-sm font-medium text-primary">Phases 14–15</p><h1 className="mt-1 text-3xl font-semibold tracking-tight">Natural language workspace</h1><p className="mt-2 text-sm text-muted-foreground">Draft transactions for review and ask controlled, read-only questions about your Ledger data.</p></div>
    {error && <p className="mt-5 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</p>}{message && <p className="mt-5 flex items-center gap-2 rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700"><CheckCircle2 className="size-4" />{message}</p>}
    <div className="mt-7 grid gap-6 lg:grid-cols-2"><Card className="h-fit"><CardHeader><CardTitle className="flex items-center gap-2"><Sparkles className="size-4" />Draft a transaction</CardTitle><p className="text-xs text-muted-foreground">No financial record is created until you review and confirm the proposal.</p></CardHeader><CardContent><form onSubmit={propose}><label className="block text-sm font-medium">What happened?<textarea className="mt-1.5 min-h-28 w-full rounded-lg border bg-white p-3 text-sm outline-none focus:ring-2 focus:ring-primary" value={text} onChange={(event) => setText(event.target.value)} placeholder="Spent $42.50 on dinner with friends yesterday." required minLength={3} maxLength={500} /></label><Button className="mt-4 w-full" disabled={loading}><Send className="mr-2 size-4" />{loading ? "Interpreting…" : "Create preview"}</Button></form></CardContent></Card>
      <Card><CardHeader><CardTitle>Review before confirming</CardTitle></CardHeader><CardContent>{!proposal ? <p className="py-12 text-center text-sm text-muted-foreground">Your structured proposal will appear here.</p> : <div className="space-y-4">{proposal.errors.length > 0 && <div className="rounded-lg bg-red-50 p-3 text-xs text-red-700">{proposal.errors.map((item) => <p key={item}>{item}</p>)}</div>}{proposal.warnings.length > 0 && <div className="rounded-lg bg-amber-50 p-3 text-xs text-amber-800">{proposal.warnings.map((item) => <p key={item}>{item}</p>)}</div>}<div className="grid grid-cols-2 gap-3"><label className="text-sm font-medium">Type<select className={`${selectClass} mt-1.5`} value={proposal.type ?? ""} onChange={(event) => { const type = event.target.value as "expense" | "income"; update("type", type); update("bucket_id", null); update("category_id", null); }}><option value="">Select</option><option value="expense">Expense</option><option value="income">Income</option></select></label><label className="text-sm font-medium">Amount CAD<Input className="mt-1.5" type="number" min="0.01" step="0.01" value={proposal.amount_cad ?? ""} onChange={(event) => update("amount_cad", event.target.value)} /></label></div><label className="block text-sm font-medium">Account<select className={`${selectClass} mt-1.5`} value={proposal.account_id ?? ""} onChange={(event) => update("account_id", event.target.value)}><option value="">Select account</option>{accounts.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label><label className="block text-sm font-medium">Date<Input className="mt-1.5" type="date" value={proposal.date} onChange={(event) => update("date", event.target.value)} /></label><label className="block text-sm font-medium">Description<Input className="mt-1.5" value={proposal.description} onChange={(event) => update("description", event.target.value)} maxLength={255} /></label><label className="block text-sm font-medium">Category<select className={`${selectClass} mt-1.5`} value={proposal.category_id ?? ""} onChange={(event) => { const id = event.target.value || null; update("category_id", id); if (proposal.type === "expense") { const category = expenseCategories.find((item) => item.id === id); update("bucket_id", category?.bucket_id ?? null); } }}><option value="">Uncategorized</option>{proposal.type === "expense" ? expenseCategories.map((item) => <option key={item.id} value={item.id}>{item.bucketName} / {item.name}</option>) : incomeCategories.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label>{proposal.type === "expense" && <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={proposal.is_major_purchase} onChange={(event) => update("is_major_purchase", event.target.checked)} /> Major purchase</label>}<Button className="w-full" disabled={loading || !proposal.ready_to_confirm || !proposal.type || !proposal.amount_cad || !proposal.account_id} onClick={() => void confirm()}>Confirm and record</Button></div>}</CardContent></Card>
    </div>
    <ReadQueryPanel />
  </div>;
}

function ReadQueryPanel() {
  const { formatMoney } = useCurrency();
  const [question, setQuestion] = useState("");
  const [response, setResponse] = useState<NaturalLanguageQueryResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function ask(event: FormEvent) {
    event.preventDefault(); setLoading(true); setError(null);
    try { setResponse(await ledgerRequest<NaturalLanguageQueryResponse>("natural-language/query", { method: "POST", body: JSON.stringify({ question }) })); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Unable to answer question"); }
    finally { setLoading(false); }
  }

  const examples = ["How much did I spend this month?", "What were my biggest purchases?", "How much did I spend on tuition?"];
  return <Card className="mt-6"><CardHeader><CardTitle className="flex items-center gap-2"><MessageCircleQuestion className="size-4" />Ask about your data</CardTitle><p className="text-xs text-muted-foreground">Read-only questions use controlled financial reports. This cannot create, edit, or delete records.</p></CardHeader><CardContent><form className="flex flex-col gap-3 sm:flex-row" onSubmit={ask}><Input value={question} onChange={(event) => setQuestion(event.target.value)} placeholder="How much did I spend this month?" required minLength={3} maxLength={500} /><Button disabled={loading}>{loading ? "Checking…" : "Ask"}</Button></form><div className="mt-3 flex flex-wrap gap-2">{examples.map((example) => <button type="button" key={example} onClick={() => setQuestion(example)} className="rounded-full border px-3 py-1 text-xs text-muted-foreground hover:bg-muted">{example}</button>)}</div>{error && <p className="mt-4 rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</p>}{response && <div className="mt-5 rounded-lg border bg-muted/30 p-4"><p className="text-sm leading-6">{response.answer}</p>{response.amount_cad !== null && <p className="mt-2 text-2xl font-semibold">{formatMoney(response.amount_cad)}</p>}{response.count !== null && <p className="mt-1 text-xs text-muted-foreground">Based on {response.count} matching record{response.count === 1 ? "" : "s"}.</p>}</div>}</CardContent></Card>;
}
