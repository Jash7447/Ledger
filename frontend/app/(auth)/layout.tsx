export default function AuthLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <main className="grid min-h-screen place-items-center px-6 py-12">
      <section className="w-full max-w-md rounded-2xl border bg-white p-8 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="grid size-10 place-items-center rounded-xl bg-primary font-bold text-primary-foreground">L</div>
          <span className="text-xl font-semibold tracking-tight">Ledger</span>
        </div>
        {children}
      </section>
    </main>
  );
}
