"use client";

import { useState } from "react";
import { Loader2, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { useSaveQuote } from "@/hooks/use-mutations";

export function AddQuoteDialog() {
  const [open, setOpen] = useState(false);
  const [text, setText] = useState("");
  const [author, setAuthor] = useState("");
  const [keywords, setKeywords] = useState("");
  const save = useSaveQuote();

  function submit(e: React.FormEvent) {
    e.preventDefault();
    save.mutate(
      {
        text,
        author: author || null,
        keywords: keywords.split(",").map((k) => k.trim()).filter(Boolean),
      },
      {
        onSuccess: () => {
          setOpen(false);
          setText("");
          setAuthor("");
          setKeywords("");
        },
      },
    );
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>
          <Plus /> Add quote
        </Button>
      </DialogTrigger>
      <DialogContent>
        <form onSubmit={submit} className="space-y-4">
          <DialogHeader>
            <DialogTitle className="font-serif text-xl italic">Add a quote</DialogTitle>
            <DialogDescription>Duplicates are detected automatically, even with different punctuation.</DialogDescription>
          </DialogHeader>
          <div className="space-y-2">
            <Label htmlFor="q-text">Quote</Label>
            <Textarea id="q-text" rows={3} required minLength={3} maxLength={300} value={text} onChange={(e) => setText(e.target.value)} className="font-serif italic" />
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="q-author">Author</Label>
              <Input id="q-author" maxLength={80} value={author} onChange={(e) => setAuthor(e.target.value)} placeholder="Optional" />
            </div>
            <div className="space-y-2">
              <Label htmlFor="q-kw">Keywords</Label>
              <Input id="q-kw" value={keywords} onChange={(e) => setKeywords(e.target.value)} placeholder="ocean, calm" />
            </div>
          </div>
          <DialogFooter>
            <Button type="submit" disabled={save.isPending || text.trim().length < 3}>
              {save.isPending && <Loader2 className="animate-spin" />} Save
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
