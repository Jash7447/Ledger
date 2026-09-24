import { AuthForm } from "@/components/auth-form";

export default function SignUpPage() {
  return (
    <>
      <h1 className="mt-8 text-2xl font-semibold tracking-tight">Create your account</h1>
      <p className="mt-2 text-sm text-muted-foreground">Your Ledger data is isolated to your authenticated account.</p>
      <AuthForm mode="signup" />
    </>
  );
}
