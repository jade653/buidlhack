"use client";

import { cn } from "@/lib/utils";
import { HTMLAttributes } from "react";

interface ArenaCardProps extends HTMLAttributes<HTMLDivElement> {
  hoverColor?: "red" | "blue";
}

export function ArenaCard({
  hoverColor = "red",
  className,
  children,
  ...props
}: ArenaCardProps) {
  const borderColor =
    hoverColor === "red" ? "hover:border-t-red" : "hover:border-t-blue";

  return (
    <div
      className={cn(
        "bg-surface border-[1.5px] border-border rounded-lg p-5 transition-all duration-200",
        "hover:-translate-y-0.5 hover:border-t-[3px]",
        borderColor,
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}
