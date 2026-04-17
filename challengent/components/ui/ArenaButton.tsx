"use client";

import { cn } from "@/lib/utils";
import { ButtonHTMLAttributes } from "react";

interface ArenaButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "red" | "blue" | "ghost";
  size?: "sm" | "md" | "lg";
}

export function ArenaButton({
  variant = "red",
  size = "md",
  className,
  children,
  ...props
}: ArenaButtonProps) {
  const base =
    "font-label uppercase tracking-[0.2em] font-semibold rounded-[4px] transition-all duration-200 cursor-pointer inline-flex items-center justify-center";

  const variants = {
    red: "bg-red text-white hover:bg-red-dark active:scale-[0.98]",
    blue: "bg-blue text-white hover:bg-blue-dark active:scale-[0.98]",
    ghost:
      "bg-transparent text-ink border-[1.5px] border-ink/20 hover:border-ink/40 hover:bg-ink/5",
  };

  const sizes = {
    sm: "px-3 py-1.5 text-xs",
    md: "px-5 py-2.5 text-sm",
    lg: "px-8 py-3.5 text-base",
  };

  return (
    <button
      className={cn(base, variants[variant], sizes[size], className)}
      {...props}
    >
      {children}
    </button>
  );
}
