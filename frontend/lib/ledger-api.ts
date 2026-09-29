export async function ledgerRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`/api/ledger/${path}`, {
    ...init,
    headers: init?.body ? { "content-type": "application/json", ...init.headers } : init?.headers
  });
  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as { detail?: string | unknown[] } | null;
    const detail = typeof payload?.detail === "string" ? payload.detail : "Request failed";
    throw new Error(detail);
  }
  return response.status === 204 ? (undefined as T) : ((await response.json()) as T);
}
