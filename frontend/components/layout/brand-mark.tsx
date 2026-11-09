import { cn } from "@/lib/utils";

export function BrandMark({ className }: { className?: string }) {
  return (
    <span
      className={cn(
        "relative grid size-9 place-items-center rounded-xl bg-gradient-to-br from-gold via-[oklch(0.75_0.14_40)] to-violet shadow-[0_8px_30px_-6px] shadow-gold/40",
        className,
      )}
    >
      <span className="font-serif text-2xl leading-none text-[oklch(0.18_0.03_60)] italic translate-y-[3px]">
        &ldquo;
      </span>
    </span>
  );
}
