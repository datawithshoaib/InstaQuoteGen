import type { Metadata } from "next";
import { Suspense } from "react";
import { PageSkeleton } from "@/components/shared/page-skeleton";
import { StudioView } from "@/components/studio/studio-view";

export const metadata: Metadata = { title: "Studio" };

export default function StudioPage() {
  return (
    <Suspense fallback={<PageSkeleton variant="studio" />}>
      <StudioView />
    </Suspense>
  );
}
