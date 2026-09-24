import { AuthForm } from "@/components/auth-form";

export default function SignInPage() {
  return (
    <>
      <h1 className="mt-8 text-2xl font-semibold tracking-tight">Welcome back</h1>
      <p className="mt-2 text-sm text-muted-foreground">Sign in to your private financial workspace.</p>
      <AuthForm mode="signin" />
    </>
  );
}
