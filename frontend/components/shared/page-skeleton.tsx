import { Skeleton } from "@/components/ui/skeleton";

/** Shown while a client page that reads the URL (useSearchParams) hydrates. */
export function PageSkeleton({ variant }: { variant: "studio" | "generate" }) {
  return (
    <div aria-busy="true" aria-label="Loading">
      <Skeleton className="mb-3 h-3 w-24" />
      <Skeleton className="mb-4 h-12 w-full max-w-md" />
      <Skeleton className="mb-10 h-4 w-full max-w-xl" />
      <div
        className={
          variant === "studio"
            ? "grid gap-8 lg:grid-cols-[minmax(0,420px)_minmax(0,1fr)]"
            : "grid gap-6 lg:grid-cols-[380px_minmax(0,1fr)]"
        }
      >
        <Skeleton className="h-[460px] rounded-2xl" />
        {variant === "studio" ? (
          <Skeleton className="mx-auto aspect-[4/5] w-full max-w-[440px] rounded-xl" />
        ) : (
          <div className="space-y-4">
            <Skeleton className="h-44 rounded-2xl" />
            <Skeleton className="h-64 rounded-2xl" />
          </div>
        )}
      </div>
    </div>
  );
}
