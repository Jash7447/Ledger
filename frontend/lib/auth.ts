import { cookies } from "next/headers";

import { serverApiUrl } from "@/lib/api";

export type CurrentUser = {
  id: string;
  email: string;
  display_name: string;
  created_at: string;
};

export async function getCurrentUser(): Promise<CurrentUser | null> {
  const cookieStore = await cookies();
  const cookieHeader = cookieStore
    .getAll()
    .map(({ name, value }) => `${name}=${value}`)
    .join("; ");

  const response = await fetch(`${serverApiUrl}/api/v1/auth/me`, {
    headers: { cookie: cookieHeader },
    cache: "no-store"
  });

  if (response.status === 401) return null;
  if (!response.ok) throw new Error("Unable to verify your session");
  return (await response.json()) as CurrentUser;
}
