import { serverApiUrl } from "@/lib/api";

const allowedActions = new Set(["signup", "login", "logout"]);

export async function POST(
  request: Request,
  context: { params: Promise<{ action: string }> }
) {
  const { action } = await context.params;
  if (!allowedActions.has(action)) {
    return Response.json({ detail: "Not found" }, { status: 404 });
  }

  const body = action === "logout" ? undefined : await request.text();
  try {
    const apiResponse = await fetch(`${serverApiUrl}/api/v1/auth/${action}`, {
      method: "POST",
      headers: body ? { "content-type": "application/json" } : undefined,
      body,
      cache: "no-store"
    });
    const responseBody = apiResponse.status === 204 ? null : await apiResponse.text();
    const headers = new Headers();
    const contentType = apiResponse.headers.get("content-type");
    const setCookie = apiResponse.headers.get("set-cookie");
    if (contentType) headers.set("content-type", contentType);
    if (setCookie) headers.set("set-cookie", setCookie);
    return new Response(responseBody, { status: apiResponse.status, headers });
  } catch {
    return Response.json({ detail: "Authentication service unavailable" }, { status: 503 });
  }
}
