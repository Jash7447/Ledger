"use client";

import { Button } from "@/components/ui/button";

export default function ProtectedError({ reset }: { reset: () => void }) {
  return (
    <main className="grid min-h-screen place-items-center px-6">
      <div className="max-w-md text-center">
        <h1 className="text-2xl font-semibold">Ledger is temporarily unavailable</h1>
        <p className="mt-3 text-sm text-muted-foreground">We could not verify your session. Make sure the backend and database are running.</p>
        <Button className="mt-6" onClick={reset}>Try again</Button>
      </div>
    </main>
  );
}
