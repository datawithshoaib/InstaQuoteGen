"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";
import { motion } from "motion/react";
import {
  AlignCenter,
  AlignLeft,
  AlignRight,
  Camera,
  Dices,
  Download,
  ExternalLink,
  Loader2,
  RectangleHorizontal,
  RectangleVertical,
  Smartphone,
  Square,
} from "lucide-react";
import { toast } from "sonner";
import { PostDialog } from "@/components/post/post-dialog";
import { ASPECT, PALETTE_CSS, PostPreview } from "@/components/post/post-preview";
import { PageHeader } from "@/components/shared/page-header";
import { ColorField } from "@/components/studio/color-field";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { useCreatePost } from "@/hooks/use-mutations";
import { useSystem } from "@/hooks/use-system";
import { api, mediaUrl } from "@/lib/api";
import type { AspectRatio, Background, Post, PostStyle } from "@/lib/types";
import { cn } from "@/lib/utils";

const DEFAULT_STYLE: PostStyle = {
  aspect_ratio: "portrait",
  font_size: 64,
  text_color: "#FFFFFF",
  accent_color: "#F5C26B",
  align: "center",
  overlay_opacity: 0.35,
  watermark: "@instaquote.studio",
  show_author: true,
  show_logo: false,
  show_quote_mark: true,
};

const SAMPLE = {
  text: "Rest is part of the climb, not a detour from it.",
  author: "",
  keywords: "misty mountain, sunrise",
};

const PREVIEW_WIDTH: Record<AspectRatio, string> = {
  portrait: "max-w-[440px]",
  square: "max-w-[500px]",
  story: "max-w-[340px]",
};

const split = (s: string) =>
  s
    .split(",")
    .map((x) => x.trim())
    .filter(Boolean);

export function StudioView() {
  const params = useSearchParams();
  const { data: system } = useSystem();
  const createPost = useCreatePost();

  const [text, setText] = useState(params.get("text") ?? SAMPLE.text);
  const [author, setAuthor] = useState(params.get("author") ?? SAMPLE.author);
  const [keywords, setKeywords] = useState(params.get("keywords")?.replaceAll(",", ", ") ?? SAMPLE.keywords);
  const hashtags = useRef(split(params.get("hashtags") ?? ""));
  const reflection = useRef(params.get("reflection"));

  const [style, setStyle] = useState<PostStyle>(DEFAULT_STYLE);
  const [background, setBackground] = useState<Background | null>(null);
  const [bgLoading, setBgLoading] = useState(false);
  const [post, setPost] = useState<Post | null>(null);

  const set = <K extends keyof PostStyle>(key: K, value: PostStyle[K]) => setStyle((s) => ({ ...s, [key]: value }));

  const loadBackground = useCallback(
    async (opts: { source: "auto" | "photo" | "gradient"; palette?: string | null; aspect?: AspectRatio }) => {
      setBgLoading(true);
      try {
        const bg = await api.backgrounds.create({
          aspect_ratio: opts.aspect ?? style.aspect_ratio,
          keywords: split(keywords),
          source: opts.source,
          palette: opts.palette ?? null,
        });
        setBackground(bg);
      } catch (err) {
        toast.error((err as Error).message);
      } finally {
        setBgLoading(false);
      }
    },
    [keywords, style.aspect_ratio],
  );

  // First background on load.
  const loaded = useRef(false);
  useEffect(() => {
    if (loaded.current) return;
    loaded.current = true;
    loadBackground({ source: "auto" });
  }, [loadBackground]);

  function changeAspect(aspect: AspectRatio) {
    set("aspect_ratio", aspect);
    // Keep the same look: re-fetch the same kind of background at the new size.
    if (background?.source === "gradient") loadBackground({ source: "gradient", palette: background.palette, aspect });
    else loadBackground({ source: "auto", aspect });
  }

  async function randomQuote() {
    try {
      const q = await api.quotes.random();
      setText(q.text);
      setAuthor(q.author ?? "");
      if (q.keywords.length) setKeywords(q.keywords.join(", "));
      hashtags.current = q.hashtags;
      reflection.current = q.reflection;
    } catch (err) {
      toast.error((err as Error).message);
    }
  }

  function exportPost() {
    createPost.mutate(
      {
        quote: {
          text,
          author: author.trim() || null,
          keywords: split(keywords),
          hashtags: hashtags.current,
          reflection: reflection.current,
        },
        style: { ...style, watermark: style.watermark?.trim() || null },
        background_id: background?.id ?? null,
      },
      {
        onSuccess: (p) => {
          setPost(p);
          toast.success("Exported. It's in your gallery too.");
        },
      },
    );
  }

  return (
    <>
      <PageHeader
        eyebrow="Studio"
        title="Design the post"
        description="Edit on the left, see it on the right. The preview uses the same font and layout rules as the exporter, so what you see is what you get."
        actions={
          <Button variant="outline" onClick={randomQuote}>
            <Dices /> Random from library
          </Button>
        }
      />

      <div className="grid gap-8 lg:grid-cols-[minmax(0,420px)_minmax(0,1fr)]">
        {/* ---------------------------------------------------------- controls */}
        <div className="glass rounded-2xl p-5">
          <Tabs defaultValue="words">
            <TabsList className="mb-5 grid w-full grid-cols-3">
              <TabsTrigger value="words">Words</TabsTrigger>
              <TabsTrigger value="type">Type</TabsTrigger>
              <TabsTrigger value="background">Background</TabsTrigger>
            </TabsList>

            <TabsContent value="words" className="space-y-5">
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label htmlFor="text">Quote</Label>
                  <span className={cn("font-mono text-xs", text.length > 280 ? "text-destructive" : "text-muted-foreground")}>
                    {text.length}/300
                  </span>
                </div>
                <Textarea
                  id="text"
                  rows={4}
                  value={text}
                  maxLength={300}
                  onChange={(e) => setText(e.target.value)}
                  className="font-serif text-base italic"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="author">Author (optional)</Label>
                <Input id="author" value={author} maxLength={80} onChange={(e) => setAuthor(e.target.value)} placeholder="Leave empty for original lines" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="keywords">Photo keywords</Label>
                <Input id="keywords" value={keywords} onChange={(e) => setKeywords(e.target.value)} placeholder="foggy forest, dawn" />
                <p className="text-xs text-muted-foreground">Comma separated. Used to search for a matching photo.</p>
              </div>
              <div className="space-y-2">
                <Label htmlFor="watermark">Handle / watermark</Label>
                <Input id="watermark" value={style.watermark ?? ""} maxLength={40} onChange={(e) => set("watermark", e.target.value)} />
              </div>
            </TabsContent>

            <TabsContent value="type" className="space-y-6">
              <div className="space-y-2">
                <Label>Format</Label>
                <ToggleGroup
                  type="single"
                  value={style.aspect_ratio}
                  onValueChange={(v) => v && changeAspect(v as AspectRatio)}
                  variant="outline"
                  className="w-full"
                >
                  <ToggleGroupItem value="portrait" className="flex-1 gap-1.5 text-xs"><RectangleVertical /> 4:5</ToggleGroupItem>
                  <ToggleGroupItem value="square" className="flex-1 gap-1.5 text-xs"><Square /> 1:1</ToggleGroupItem>
                  <ToggleGroupItem value="story" className="flex-1 gap-1.5 text-xs"><Smartphone /> 9:16</ToggleGroupItem>
                </ToggleGroup>
              </div>

              <div className="space-y-3">
                <div className="flex justify-between">
                  <Label>Text size</Label>
                  <span className="font-mono text-xs text-muted-foreground">{style.font_size}px</span>
                </div>
                <Slider min={28} max={120} step={2} value={[style.font_size]} onValueChange={([v]) => set("font_size", v)} />
              </div>

              <div className="space-y-2">
                <Label>Alignment</Label>
                <ToggleGroup type="single" value={style.align} onValueChange={(v) => v && set("align", v as PostStyle["align"])} variant="outline">
                  <ToggleGroupItem value="left" aria-label="Align left"><AlignLeft /></ToggleGroupItem>
                  <ToggleGroupItem value="center" aria-label="Align center"><AlignCenter /></ToggleGroupItem>
                  <ToggleGroupItem value="right" aria-label="Align right"><AlignRight /></ToggleGroupItem>
                </ToggleGroup>
              </div>

              <ColorField label="Text colour" value={style.text_color} swatches={["#FFFFFF", "#F6EFE3", "#F5C26B", "#111111"]} onChange={(v) => set("text_color", v)} />
              <ColorField label="Accent colour" value={style.accent_color} swatches={["#F5C26B", "#FF8A65", "#7FE0C2", "#B9A6FF", "#FFFFFF"]} onChange={(v) => set("accent_color", v)} />

              <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
                {(
                  [
                    ["show_quote_mark", "Quote mark"],
                    ["show_author", "Author"],
                    ["show_logo", "Logo"],
                  ] as const
                ).map(([key, label]) => (
                  <label key={key} className="flex items-center justify-between gap-2 rounded-lg border border-border px-3 py-2 text-sm">
                    {label}
                    <Switch checked={style[key]} onCheckedChange={(v) => set(key, v)} />
                  </label>
                ))}
              </div>
            </TabsContent>

            <TabsContent value="background" className="space-y-6">
              <div className="space-y-2">
                <Label>Photo</Label>
                <Button
                  variant="outline"
                  className="w-full"
                  disabled={bgLoading || !system?.images.enabled}
                  onClick={() => loadBackground({ source: "photo" })}
                >
                  {bgLoading ? <Loader2 className="animate-spin" /> : <Camera />}
                  {system?.images.enabled ? "Find another photo" : "Photos need an Unsplash key"}
                </Button>
                {!system?.images.enabled && (
                  <p className="text-xs text-muted-foreground">
                    Add <code className="font-mono">UNSPLASH_ACCESS_KEY</code> to backend/.env for real photography.
                  </p>
                )}
              </div>

              <div className="space-y-2">
                <Label>Gradient</Label>
                <div className="grid grid-cols-3 gap-2">
                  {Object.entries(PALETTE_CSS).map(([name, css]) => (
                    <button
                      key={name}
                      type="button"
                      onClick={() => loadBackground({ source: "gradient", palette: name })}
                      className={cn(
                        "relative h-16 overflow-hidden rounded-lg ring-1 ring-white/10 transition hover:ring-gold/60",
                        background?.palette === name && "ring-2 ring-gold",
                      )}
                      style={{ background: css }}
                    >
                      <span className="absolute bottom-1 left-2 text-[11px] capitalize text-white/85">{name}</span>
                    </button>
                  ))}
                </div>
              </div>

              <div className="space-y-3">
                <div className="flex justify-between">
                  <Label>Darken</Label>
                  <span className="font-mono text-xs text-muted-foreground">{Math.round(style.overlay_opacity * 100)}%</span>
                </div>
                <Slider min={0} max={0.9} step={0.05} value={[style.overlay_opacity]} onValueChange={([v]) => set("overlay_opacity", v)} />
              </div>
            </TabsContent>
          </Tabs>
        </div>

        {/* ----------------------------------------------------------- preview */}
        <div className="flex flex-col items-center gap-4 lg:sticky lg:top-24 lg:self-start">
          <motion.div
            layout
            transition={{ type: "spring", bounce: 0.15, duration: 0.6 }}
            className={cn("relative w-full", PREVIEW_WIDTH[style.aspect_ratio])}
            style={{ aspectRatio: ASPECT[style.aspect_ratio] }}
          >
            <div className="absolute -inset-2 -z-10 rounded-[2rem] sm:-inset-6 bg-gradient-to-br from-gold/20 via-transparent to-violet/25 blur-2xl" />
            <PostPreview
              text={text}
              author={author}
              style={style}
              backgroundUrl={background && background.aspect_ratio === style.aspect_ratio ? mediaUrl(background.url) : null}
              palette={background?.palette}
              className="rounded-xl shadow-2xl ring-1 ring-white/10"
            />
            {bgLoading && (
              <div className="absolute inset-0 grid place-items-center rounded-xl bg-black/30 backdrop-blur-[2px]">
                <Loader2 className="size-6 animate-spin text-gold" />
              </div>
            )}
          </motion.div>

          {background?.credit && (
            <p className="text-xs text-muted-foreground">
              Photo by{" "}
              <a href={background.credit.profile_url ?? "#"} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-foreground hover:underline">
                {background.credit.name} <ExternalLink className="size-3" />
              </a>{" "}
              on Unsplash
            </p>
          )}

          <div className={cn("flex w-full gap-2", PREVIEW_WIDTH[style.aspect_ratio])}>
            <Button variant="outline" onClick={() => loadBackground({ source: background?.source === "gradient" ? "gradient" : "auto" })} disabled={bgLoading}>
              <RectangleHorizontal /> New background
            </Button>
            <Button
              className="flex-1 bg-gradient-to-r from-gold to-[oklch(0.78_0.14_50)] font-semibold"
              onClick={exportPost}
              disabled={createPost.isPending || text.trim().length < 3}
            >
              {createPost.isPending ? <Loader2 className="animate-spin" /> : <Download />} Export PNG
            </Button>
          </div>
        </div>
      </div>

      <PostDialog post={post} open={!!post} onOpenChange={(o) => !o && setPost(null)} />
    </>
  );
}
