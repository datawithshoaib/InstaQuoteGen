import type { Metadata } from "next";
import { GalleryView } from "@/components/gallery/gallery-view";

export const metadata: Metadata = { title: "Gallery" };

export default function GalleryPage() {
  return <GalleryView />;
}
