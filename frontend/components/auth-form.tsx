"use client";

import Link from "next/link";
import { useState, type FormEvent } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

type AuthFormProps = { mode: "signin" | "signup" };

function getErrorMessage(payload: unknown): string {
  if (typeof payload === "object" && payload !== null && "detail" in payload) {
    const detail = (payload as { detail: unknown }).detail;
    if (typeof detail === "string") return detail;
  }
  return "Something went wrong. Please try again.";
}

export function AuthForm({ mode }: AuthFormProps) {
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const isSignup = mode === "signup";

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);

    const form = new FormData(event.currentTarget);
    const payload = {
      email: String(form.get("email") ?? ""),
      password: String(form.get("password") ?? ""),
      ...(isSignup ? { display_name: String(form.get("display_name") ?? "") } : {})
    };

    try {
      const response = await fetch(`/api/auth/${isSignup ? "signup" : "login"}`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(payload)
      });
      if (!response.ok) {
        setError(getErrorMessage(await response.json()));
        return;
      }
      window.location.assign("/");
    } catch {
      setError("The authentication service is unavailable.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form className="mt-8 space-y-5" onSubmit={handleSubmit}>
      {isSignup && (
        <div className="space-y-2">
          <label className="text-sm font-medium" htmlFor="display_name">Name</label>
          <Input id="display_name" name="display_name" autoComplete="name" minLength={1} maxLength={100} required />
        </div>
      )}
      <div className="space-y-2">
        <label className="text-sm font-medium" htmlFor="email">Email</label>
        <Input id="email" name="email" type="email" autoComplete="email" required />
      </div>
      <div className="space-y-2">
        <label className="text-sm font-medium" htmlFor="password">Password</label>
        <Input
          id="password"
          name="password"
          type="password"
          autoComplete={isSignup ? "new-password" : "current-password"}
          minLength={isSignup ? 8 : 1}
          maxLength={128}
          required
        />
        {isSignup && <p className="text-xs text-muted-foreground">Use at least 8 characters.</p>}
      </div>
      {error && <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700" role="alert">{error}</p>}
      <Button className="w-full" type="submit" disabled={submitting}>
        {submitting ? "Please wait…" : isSignup ? "Create account" : "Sign in"}
      </Button>
      <p className="text-center text-sm text-muted-foreground">
        {isSignup ? "Already have an account?" : "New to Ledger?"}{" "}
        <Link className="font-medium text-primary hover:underline" href={isSignup ? "/sign-in" : "/sign-up"}>
          {isSignup ? "Sign in" : "Create an account"}
        </Link>
      </p>
    </form>
  );
}
