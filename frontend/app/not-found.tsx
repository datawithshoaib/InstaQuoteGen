import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function NotFound() {
  return (
    <div className="flex flex-col items-center gap-4 py-32 text-center">
      <p className="font-serif text-8xl text-gold/40 italic">&ldquo;404&rdquo;</p>
      <h1 className="font-serif text-3xl italic">Not every page makes the cut.</h1>
      <Button asChild variant="outline">
        <Link href="/">Back home</Link>
      </Button>
    </div>
  );
}
