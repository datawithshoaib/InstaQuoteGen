"use client";

import { useState } from "react";
import { Check, Copy } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";

export function CopyButton({
  value,
  label = "Copy",
  variant = "outline",
  size = "sm",
}: {
  value: string;
  label?: string;
  variant?: "outline" | "ghost" | "secondary" | "default";
  size?: "sm" | "default" | "icon-sm";
}) {
  const [copied, setCopied] = useState(false);

  async function copy() {
    try {
      await navigator.clipboard.writeText(value);
      setCopied(true);
      setTimeout(() => setCopied(false), 1600);
    } catch {
      toast.error("Clipboard is blocked in this browser.");
    }
  }

  return (
    <Button variant={variant} size={size} onClick={copy} aria-label={label}>
      {copied ? <Check className="text-success" /> : <Copy />}
      {size !== "icon-sm" && (copied ? "Copied" : label)}
    </Button>
  );
}
