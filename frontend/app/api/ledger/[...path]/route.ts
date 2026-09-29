import { serverApiUrl } from "@/lib/api";

const allowedResources = new Set(["accounts", "transactions", "classifications", "dashboard", "budgets", "recurring", "education", "people", "settings", "analytics", "goals", "natural-language"]);

async function proxy(request: Request, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  if (!path.length || !allowedResources.has(path[0])) {
    return Response.json({ detail: "Not found" }, { status: 404 });
  }

  const incomingUrl = new URL(request.url);
  const target = `${serverApiUrl}/api/v1/${path.map(encodeURIComponent).join("/")}${incomingUrl.search}`;
  const body = request.method === "GET" || request.method === "HEAD" ? undefined : await request.text();
  const headers = new Headers();
  const cookie = request.headers.get("cookie");
  const contentType = request.headers.get("content-type");
  if (cookie) headers.set("cookie", cookie);
  if (contentType) headers.set("content-type", contentType);

  try {
    const apiResponse = await fetch(target, {
      method: request.method,
      headers,
      body: body || undefined,
      cache: "no-store"
    });
    const responseHeaders = new Headers();
    const responseType = apiResponse.headers.get("content-type");
    if (responseType) responseHeaders.set("content-type", responseType);
    return new Response(apiResponse.status === 204 ? null : await apiResponse.text(), {
      status: apiResponse.status,
      headers: responseHeaders
    });
  } catch {
    return Response.json({ detail: "Ledger API unavailable" }, { status: 503 });
  }
}

export const GET = proxy;
export const POST = proxy;
export const PATCH = proxy;
export const DELETE = proxy;
