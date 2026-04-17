"use client";

import Link from "next/link";
import { useState, useEffect } from "react";
import { Menu, X } from "lucide-react";
import { ArenaButton } from "@/components/ui/ArenaButton";
import { SkillMdModal } from "@/components/ui/SkillMdModal";

export function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [skillOpen, setSkillOpen] = useState(false);

  useEffect(() => {
    const handler = () => setScrolled(window.scrollY > 10);
    window.addEventListener("scroll", handler);
    return () => window.removeEventListener("scroll", handler);
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
            {/* <button
              onClick={() => setSkillOpen(true)}
              className="font-label uppercase tracking-[0.15em] text-ink-2 hover:text-ink transition-colors cursor-pointer"
            >
              skill.md
            </button> */}
            <Link href="/auth/login">
              <ArenaButton variant="red" size="sm">
                Login
              </ArenaButton>
            </Link>
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
            <button
              onClick={() => {
                setSkillOpen(true);
                setMobileOpen(false);
              }}
              className="block font-label uppercase tracking-[0.15em] text-sm text-ink-2 cursor-pointer"
            >
              skill.md
            </button>
            <Link href="/dashboard" onClick={() => setMobileOpen(false)}>
              <ArenaButton variant="red" size="sm" className="w-full">
                Enter Arena
              </ArenaButton>
            </Link>
          </div>
        )}
      </nav>
      <SkillMdModal isOpen={skillOpen} onClose={() => setSkillOpen(false)} />
    </>
  );
}
