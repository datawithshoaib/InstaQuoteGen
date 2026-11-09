"use client";

import { Cpu, ImageIcon, WifiOff } from "lucide-react";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { useSystem } from "@/hooks/use-system";
import { cn } from "@/lib/utils";

function Pill({ on, icon: Icon, label, tip }: { on: boolean; icon: typeof Cpu; label: string; tip: string }) {
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <span
          className={cn(
            "hidden items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs lg:inline-flex",
            on ? "border-success/25 bg-success/10 text-success" : "border-warning/25 bg-warning/10 text-warning",
          )}
        >
          <span className={cn("size-1.5 rounded-full", on ? "bg-success" : "bg-warning")} />
          <Icon className="size-3.5" />
          {label}
        </span>
      </TooltipTrigger>
      <TooltipContent>{tip}</TooltipContent>
    </Tooltip>
  );
}

export function StatusPills() {
  const { data, isError } = useSystem();

  if (isError) {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full border border-destructive/30 bg-destructive/10 px-2.5 py-1 text-xs text-destructive">
        <WifiOff className="size-3.5" /> API offline
      </span>
    );
  }
  if (!data) return null;

  return (
    <div className="flex items-center gap-2">
      <Pill
        on={data.llm.enabled}
        icon={Cpu}
        label={data.llm.enabled ? "AI on" : "Library mode"}
        tip={data.llm.enabled ? data.llm.detail : "No GROQ_API_KEY set: generation uses your quote library."}
      />
      <Pill
        on={data.images.enabled}
        icon={ImageIcon}
        label={data.images.enabled ? "Unsplash" : "Gradients"}
        tip={data.images.enabled ? "Backgrounds come from Unsplash" : "No UNSPLASH_ACCESS_KEY set: using generated gradients."}
      />
    </div>
  );
}
