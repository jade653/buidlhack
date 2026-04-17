"use client";

import {
  cloneElement,
  isValidElement,
  useMemo,
  useState,
  type ReactElement,
  type ReactNode,
} from "react";
import { useSearchParams } from "next/navigation";
import { createSupabaseBrowserClient } from "@/lib/supabase/client";
import { ArenaButton } from "@/components/ui/ArenaButton";

type LoginFormProps = {
  children?: ReactNode;
  /** Nav 등에서 넘기면 이 경로로 돌아옴 (?next= 대신) */
  nextPath?: string;
};

export function LoginForm({ children, nextPath }: LoginFormProps) {
  const searchParams = useSearchParams();
  const next = useMemo(() => {
    if (nextPath?.startsWith("/")) return nextPath;
    const n = searchParams.get("next");
    if (!n || !n.startsWith("/")) return "/";
    return n;
  }, [nextPath, searchParams]);
  const error = searchParams.get("error");
  const [loading, setLoading] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);

  const signInWithGitHub = async () => {
    setLocalError(null);
    setLoading(true);
    try {
      const supabase = createSupabaseBrowserClient();
      const origin = window.location.origin;
      const redirectTo = `${origin}/auth/callback?next=${encodeURIComponent(next)}`;
      const { error: oauthError } = await supabase.auth.signInWithOAuth({
        provider: "github",
        options: { redirectTo },
      });
      if (oauthError) {
        setLocalError(oauthError.message);
        setLoading(false);
      }
    } catch (e) {
      setLocalError(
        e instanceof Error ? e.message : "로그인을 시작할 수 없습니다.",
      );
      setLoading(false);
    }
  };

  const trigger =
    children && isValidElement(children) ? (
      cloneElement(
        children as ReactElement<{ onClick?: () => void; disabled?: boolean }>,
        {
          onClick: () => {
            (
              children as ReactElement<{ onClick?: () => void }>
            ).props.onClick?.();
            void signInWithGitHub();
          },
          disabled:
            loading ||
            !!(children as ReactElement<{ disabled?: boolean }>).props.disabled,
        },
      )
    ) : (
      <ArenaButton
        variant="red"
        size="lg"
        className="w-full"
        disabled={loading}
        onClick={() => void signInWithGitHub()}
      >
        {loading ? "Redirecting to GitHub…" : "Continue with GitHub"}
        <div className="ml-2 rounded-full bg-white w-6 h-6 flex justify-center items-center">
          <img
            src="/assets/github.png"
            alt="GitHub"
            className="w-5 h-5 inline"
            style={{ verticalAlign: "middle" }}
          />
        </div>
      </ArenaButton>
    );

  return (
    <div
      className={
        children
          ? "inline-flex flex-col gap-2"
          : "pt-28 max-w-lg mx-auto px-6 pb-16"
      }
    >
      {trigger}
      {(error || localError) && (
        <div className="rounded-lg border border-red/30 bg-red/5 px-4 py-3 text-sm text-red">
          {localError || error}
        </div>
      )}
    </div>
  );
}
