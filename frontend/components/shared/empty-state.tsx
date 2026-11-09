import type { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
  className,
}: {
  icon: LucideIcon;
  title: string;
  description?: string;
  action?: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "glass flex flex-col items-center justify-center gap-3 rounded-2xl px-6 py-16 text-center",
        className,
      )}
    >
      <span className="grid size-12 place-items-center rounded-2xl bg-white/5 ring-1 ring-white/10">
        <Icon className="size-5 text-gold" />
      </span>
      <h3 className="font-serif text-xl italic">{title}</h3>
      {description && <p className="max-w-sm text-sm text-muted-foreground">{description}</p>}
      {action && <div className="mt-2">{action}</div>}
    </div>
  );
}
