import { Suspense } from "react";
import { LoginForm } from "./LoginForm";

export default function AuthLoginPage() {
  return (
    <Suspense
      fallback={
        <div className="pt-28 max-w-lg mx-auto px-6 pb-16 text-sm text-ink-2">
          로딩 중…
        </div>
      }
    >
      <LoginForm />
    </Suspense>
  );
}
