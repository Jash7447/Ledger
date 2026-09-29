"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

import { ledgerRequest } from "@/lib/ledger-api";
import type { CurrencySettings, DisplayCurrency } from "@/lib/ledger-types";

type CurrencyContextValue = {
  settings: CurrencySettings;
  loading: boolean;
  saving: boolean;
  error: string | null;
  formatMoney: (cadValue: string | number) => string;
  updateSettings: (changes: Partial<Pick<CurrencySettings, "display_currency" | "cad_to_inr_rate">>) => Promise<void>;
  toggleCurrency: () => Promise<void>;
};

const defaults: CurrencySettings = { display_currency: "CAD", cad_to_inr_rate: "70.0000", updated_at: "" };
const CurrencyContext = createContext<CurrencyContextValue | null>(null);

export function CurrencyProvider({ children }: { children: React.ReactNode }) {
  const [settings, setSettings] = useState<CurrencySettings>(defaults);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void ledgerRequest<CurrencySettings>("settings/currency")
      .then((value) => { setSettings(value); setError(null); })
      .catch((reason) => setError(reason instanceof Error ? reason.message : "Unable to load currency settings"))
      .finally(() => setLoading(false));
  }, []);

  const updateSettings = useCallback(async (changes: Partial<Pick<CurrencySettings, "display_currency" | "cad_to_inr_rate">>) => {
    setSaving(true); setError(null);
    try {
      setSettings(await ledgerRequest<CurrencySettings>("settings/currency", { method: "PATCH", body: JSON.stringify(changes) }));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to update currency settings");
      throw reason;
    } finally { setSaving(false); }
  }, []);

  const toggleCurrency = useCallback(async () => {
    const display_currency: DisplayCurrency = settings.display_currency === "CAD" ? "INR" : "CAD";
    await updateSettings({ display_currency });
  }, [settings.display_currency, updateSettings]);

  const formatMoney = useCallback((cadValue: string | number) => {
    const cad = Number(cadValue);
    const value = settings.display_currency === "INR" ? cad * Number(settings.cad_to_inr_rate) : cad;
    return new Intl.NumberFormat(settings.display_currency === "INR" ? "en-IN" : "en-CA", {
      style: "currency",
      currency: settings.display_currency,
      maximumFractionDigits: 2
    }).format(value);
  }, [settings]);

  const value = useMemo(() => ({ settings, loading, saving, error, formatMoney, updateSettings, toggleCurrency }), [settings, loading, saving, error, formatMoney, updateSettings, toggleCurrency]);
  return <CurrencyContext.Provider value={value}>{children}</CurrencyContext.Provider>;
}

export function useCurrency() {
  const context = useContext(CurrencyContext);
  if (!context) throw new Error("useCurrency must be used within CurrencyProvider");
  return context;
}
