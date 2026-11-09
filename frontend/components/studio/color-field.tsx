"use client";

import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";

export function ColorField({
  label,
  value,
  swatches,
  onChange,
}: {
  label: string;
  value: string;
  swatches: string[];
  onChange: (hex: string) => void;
}) {
  return (
    <div className="space-y-2">
      <Label>{label}</Label>
      <div className="flex flex-wrap items-center gap-2">
        {swatches.map((hex) => (
          <button
            key={hex}
            type="button"
            aria-label={`${label} ${hex}`}
            onClick={() => onChange(hex)}
            className={cn(
              "size-7 rounded-full ring-1 ring-white/15 transition hover:scale-110",
              value.toLowerCase() === hex.toLowerCase() && "ring-2 ring-gold ring-offset-2 ring-offset-background",
            )}
            style={{ background: hex }}
          />
        ))}
        <label className="relative grid size-7 cursor-pointer place-items-center overflow-hidden rounded-full bg-[conic-gradient(red,yellow,lime,cyan,blue,magenta,red)] ring-1 ring-white/15">
          <input
            type="color"
            value={value}
            onChange={(e) => onChange(e.target.value.toUpperCase())}
            className="absolute inset-0 cursor-pointer opacity-0"
            aria-label={`Custom ${label.toLowerCase()}`}
          />
        </label>
        <span className="font-mono text-xs text-muted-foreground">{value}</span>
      </div>
    </div>
  );
}
