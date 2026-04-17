"use client";

import Link from "next/link";
import { Suspense, useState, useEffect } from "react";
import { usePathname } from "next/navigation";
import { Menu, X } from "lucide-react";
import type { User } from "@supabase/supabase-js";
import { ArenaButton } from "@/components/ui/ArenaButton";
import { LoginForm } from "@/app/auth/login/LoginForm";
import { createSupabaseBrowserClient } from "@/lib/supabase/client";

function displayName(user: User) {
  const meta = user.user_metadata as { user_name?: string } | undefined;
  return meta?.user_name || user.email || user.id;
}

export function Navbar() {
  const pathname = usePathname();
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [user, setUser] = useState<User | null>(null);
  const [authReady, setAuthReady] = useState(false);
  const [remainingCredits, setRemainingCredits] = useState<number | null>(null);

  const fetchMyCredits = async () => {
    const response = await fetch("/api/credits/me", {
      credentials: "include",
      cache: "no-store",
    });
    if (!response.ok) return;
    const data = (await response.json()) as { credits?: number };
    setRemainingCredits(typeof data.credits === "number" ? data.credits : null);
  };

  useEffect(() => {
    const handler = () => setScrolled(window.scrollY > 10);
    window.addEventListener("scroll", handler);
    return () => window.removeEventListener("scroll", handler);
  }, []);

  useEffect(() => {
    let subscription: { unsubscribe: () => void } | undefined;
    (async () => {
      try {
        const supabase = createSupabaseBrowserClient();
        const {
          data: { user: current },
        } = await supabase.auth.getUser();
        setUser(current);
        if (current) {
          await fetchMyCredits();
        }
        const {
          data: { subscription: sub },
        } = supabase.auth.onAuthStateChange((_event, session) => {
          setUser(session?.user ?? null);
          if (session?.user) {
            void fetchMyCredits();
          } else {
            setRemainingCredits(null);
          }
        });
        subscription = sub;
      } catch {
        setUser(null);
        setRemainingCredits(null);
      } finally {
        setAuthReady(true);
      }
    })();
    return () => subscription?.unsubscribe();
  }, []);

  return (
    <>
      <nav
        className={`fixed top-0 left-0 right-0 z-40 transition-all duration-200 ${
          scrolled
            ? "bg-bg/80 backdrop-blur-md border-b border-border"
            : "bg-transparent"
        }`}
      >
        <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
          <Link
            href="/"
            className="flex flex-col gap-0 items-center leading-tight"
          >
            <div className="flex items-baseline gap-0 leading-tight mb-[-6px]">
              <img
                src="/assets/glove.png"
                alt="Forgent Glove Logo"
                className="h-6 mr-1"
              />
              <span className="font-title text-3xl text-ink leading-tight">
                Challen
              </span>
              <span className="font-title text-3xl text-red leading-tight">
                gent
              </span>
            </div>
            <span className="font-label text-sm text-ink-3 leading-tight">
              The Sparring Arena
            </span>
          </Link>

          <div className="hidden md:flex items-center gap-8">
            <Link
              href="/dashboard"
              className="font-label uppercase tracking-[0.15em] text-ink-2 hover:text-ink transition-colors"
            >
              Challenges
            </Link>
            <Link
              href="/leaderboard"
              className="font-label uppercase tracking-[0.15em] text-ink-2 hover:text-ink transition-colors"
            >
              Leaderboard
            </Link>
            <Link
              href="/skill"
              className="font-label uppercase tracking-[0.15em] text-ink-2 hover:text-ink transition-colors"
            >
              Docs
            </Link>
            {authReady && user ? (
              <div className="flex items-center gap-3">
                <div className="font-label flex gap-2 rounded-md bg-red text-white py-1 px-2 text-white items-center">
                  <span className="max-w-[140px] truncate">
                    {displayName(user)}
                  </span>
                  <span>|</span>
                  <span>{remainingCredits ?? "—"} CREDIT</span>
                </div>
                <form action="/auth/signout" method="POST">
                  <ArenaButton type="submit" variant="ghost" size="sm">
                    Logout
                  </ArenaButton>
                </form>
              </div>
            ) : (
              <Suspense
                fallback={
                  <ArenaButton variant="red" size="sm">
                    {authReady ? "Login" : "…"}
                  </ArenaButton>
                }
              >
                <LoginForm nextPath={pathname}>
                  <ArenaButton variant="red" size="sm" type="button">
                    {authReady ? "Login" : "…"}
                  </ArenaButton>
                </LoginForm>
              </Suspense>
            )}
          </div>
          <button
            className="md:hidden text-ink cursor-pointer"
            onClick={() => setMobileOpen(!mobileOpen)}
          >
            {mobileOpen ? (
              <X className="w-6 h-6" />
            ) : (
              <Menu className="w-6 h-6" />
            )}
          </button>
        </div>

        {mobileOpen && (
          <div className="md:hidden bg-surface border-b border-border p-4 space-y-3">
            <Link
              href="/dashboard"
              className="block font-label uppercase tracking-[0.15em] text-sm text-ink-2"
              onClick={() => setMobileOpen(false)}
            >
              Challenges
            </Link>
            <Link
              href="/leaderboard"
              className="block font-label uppercase tracking-[0.15em] text-sm text-ink-2"
              onClick={() => setMobileOpen(false)}
            >
              Leaderboard
            </Link>
            <Link
              href="/skill"
              className="block font-label uppercase tracking-[0.15em] text-sm text-ink-2"
              onClick={() => setMobileOpen(false)}
            >
              Docs
            </Link>
            {authReady && user ? (
              <div className="space-y-2 pt-2 border-t border-border">
                <p className="text-xs text-ink-2 truncate">
                  {displayName(user)}
                </p>
                <p className="text-xs text-ink-3">
                  {remainingCredits ?? "—"} CR
                </p>
                <form action="/auth/signout" method="POST">
                  <ArenaButton
                    type="submit"
                    variant="ghost"
                    size="sm"
                    className="w-full"
                  >
                    로그아웃
                  </ArenaButton>
                </form>
              </div>
            ) : (
              <Suspense
                fallback={
                  <ArenaButton variant="red" size="sm" className="w-full">
                    Login
                  </ArenaButton>
                }
              >
                <LoginForm nextPath={pathname}>
                  <ArenaButton
                    variant="red"
                    size="sm"
                    className="w-full"
                    type="button"
                    onClick={() => setMobileOpen(false)}
                  >
                    Login
                  </ArenaButton>
                </LoginForm>
              </Suspense>
            )}
          </div>
        )}
      </nav>
    </>
  );
}
