"use client";

import { useEffect, useRef, useState } from "react";
import { ArrowUp } from "lucide-react";
import { cn } from "@/lib/utils";

const MAX = 2000;

interface Props {
  onSend: (text: string) => void;
  disabled: boolean;
  placeholder: string;
}

export default function ChatInput({ onSend, disabled, placeholder }: Props) {
  const [value, setValue] = useState("");
  const ref = useRef<HTMLTextAreaElement>(null);

  // Auto-grow up to ~6 lines.
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
  }, [value]);

  const submit = () => {
    if (disabled || !value.trim()) return;
    onSend(value);
    setValue("");
  };

  return (
    <div className="flex items-end gap-2 rounded-2xl border border-rule bg-paper-raised p-2 focus-within:border-pine">
      <textarea
        ref={ref}
        rows={1}
        value={value}
        maxLength={MAX}
        disabled={disabled}
        placeholder={placeholder}
        aria-label="Your question"
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            submit();
          }
        }}
        className="max-h-40 flex-1 resize-none bg-transparent px-2 py-1.5 outline-none placeholder:text-ink-faint disabled:cursor-not-allowed"
      />
      <button
        onClick={submit}
        disabled={disabled || !value.trim()}
        aria-label="Send question"
        className={cn(
          "flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-white transition-colors",
          disabled || !value.trim() ? "bg-ink-faint/50" : "bg-pine hover:bg-pine-dark",
        )}
      >
        <ArrowUp className="h-5 w-5" />
      </button>
    </div>
  );
}
