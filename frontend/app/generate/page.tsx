import type { Metadata } from "next";
import { Suspense } from "react";
import { PageSkeleton } from "@/components/shared/page-skeleton";
import { GenerateView } from "@/components/generate/generate-view";

export const metadata: Metadata = { title: "Generate" };

export default function GeneratePage() {
  return (
    <Suspense fallback={<PageSkeleton variant="generate" />}>
      <GenerateView />
    </Suspense>
  );
}
