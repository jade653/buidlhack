"use client";

import { useEffect } from "react";
import ReactMarkdown from "react-markdown";
import { X } from "lucide-react";
import { SKILL_MD } from "@/lib/skill-md";

interface SkillMdModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function SkillMdModal({ isOpen, onClose }: SkillMdModalProps) {
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />
      <div className="relative bg-surface rounded-lg border border-border max-w-2xl w-full max-h-[80vh] overflow-y-auto p-8">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-ink-2 hover:text-ink cursor-pointer"
        >
          <X className="w-5 h-5" />
        </button>
        <div className="prose prose-sm max-w-none prose-headings:font-title prose-code:bg-ink/5 prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded prose-pre:bg-ink/5 prose-pre:rounded-lg">
          <ReactMarkdown>{SKILL_MD}</ReactMarkdown>
        </div>
      </div>
    </div>
  );
}
