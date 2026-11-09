/* eslint-disable @next/next/no-img-element -- media comes from the API, not the Next image pipeline */
import type { CSSProperties } from "react";
import type { AspectRatio, PostStyle } from "@/lib/types";
import { cn } from "@/lib/utils";

/**
 * A live CSS replica of the backend renderer (backend/app/services/renderer.py).
 * Sizes are expressed as fractions of a 1080px-wide canvas and converted to
 * container-query units, so the preview scales to any width and still matches
 * the exported PNG: same font, same proportions, same balanced line wrapping.
 */

const CANVAS = 1080;
const cq = (px: number) => `${((px / CANVAS) * 100).toFixed(3)}cqw`;

export const ASPECT: Record<AspectRatio, string> = {
  portrait: "4 / 5",
  square: "1 / 1",
  story: "9 / 16",
};

export const PALETTE_CSS: Record<string, string> = {
  aurora: "radial-gradient(60% 40% at 35% 28%, #4a3b9a99, transparent 70%), linear-gradient(#0c0a26, #18405c)",
  ember: "radial-gradient(60% 40% at 60% 25%, #b8603899, transparent 70%), linear-gradient(#1c0a12, #5c1e18)",
  ocean: "radial-gradient(60% 40% at 40% 30%, #2a7fae99, transparent 70%), linear-gradient(#061226, #0a3a5c)",
  forest: "radial-gradient(60% 40% at 55% 30%, #4f855799, transparent 70%), linear-gradient(#081612, #183a2c)",
  dusk: "radial-gradient(60% 40% at 45% 25%, #b8737099, transparent 70%), linear-gradient(#1a0e2c, #6e2e58)",
  mono: "radial-gradient(60% 40% at 50% 30%, #6e6e7699, transparent 70%), linear-gradient(#0e0e10, #28282e)",
};

interface PostPreviewProps {
  text: string;
  author?: string | null;
  style: PostStyle;
  backgroundUrl?: string | null;
  palette?: string | null;
  className?: string;
}

export function PostPreview({ text, author, style, backgroundUrl, palette, className }: PostPreviewProps) {
  const size = style.font_size;
  const textAlign = style.align;
  const showAuthor = style.show_author && !!author?.trim();

  const shell: CSSProperties = {
    aspectRatio: ASPECT[style.aspect_ratio],
    containerType: "inline-size",
    background: backgroundUrl ? undefined : PALETTE_CSS[palette ?? "aurora"] ?? PALETTE_CSS.aurora,
  };

  return (
    <div className={cn("relative w-full overflow-hidden bg-black select-none", className)} style={shell}>
      {backgroundUrl && (
        <img src={backgroundUrl} alt="" className="absolute inset-0 size-full object-cover" draggable={false} />
      )}

      {/* scrim: flat darkening + vignette, same numbers as the renderer */}
      <div className="absolute inset-0" style={{ background: `rgba(0,0,0,${style.overlay_opacity})` }} />
      <div
        className="absolute inset-0"
        style={{
          background:
            "linear-gradient(to bottom, rgba(0,0,0,.27) 0%, rgba(0,0,0,.05) 22%, transparent 40%, transparent 60%, rgba(0,0,0,.05) 78%, rgba(0,0,0,.27) 100%)",
        }}
      />

      <div
        className="absolute inset-0 flex flex-col justify-center font-serif italic"
        style={{
          paddingInline: cq(CANVAS * 0.1),
          transform: "translateY(-2%)",
          textAlign,
          textShadow: `0 0 ${cq(size * 0.28)} rgba(0,0,0,.6)`,
        }}
      >
        {style.show_quote_mark && (
          <div style={{ height: cq(size * 2.2 * 0.55), color: style.accent_color }}>
            <span
              className="block leading-none"
              style={{ fontSize: cq(size * 2.2), transform: `translateY(-${cq(size * 2.2 * 0.18)})` }}
            >
              &ldquo;
            </span>
          </div>
        )}
        <p
          className="break-words"
          style={{ fontSize: cq(size), lineHeight: 1.28, color: style.text_color, textWrap: "balance" }}
        >
          {text || "Your words go here."}
        </p>
        {showAuthor && (
          <p style={{ fontSize: cq(Math.max(24, size * 0.42)), marginTop: cq(size * 0.45), color: style.accent_color }}>
            &mdash; {author}
          </p>
        )}
      </div>

      {(style.watermark || style.show_logo) && (
        <div
          className="absolute inset-x-0 flex flex-col items-center font-serif italic"
          style={{ bottom: "5.5%", gap: cq(16) }}
        >
          {style.show_logo && (
            <img src="/logo.png" alt="" className="rounded-full" style={{ width: cq(84), height: cq(84) }} />
          )}
          {style.watermark && (
            <span className="leading-none text-white/75" style={{ fontSize: cq(30) }}>
              {style.watermark}
            </span>
          )}
        </div>
      )}
    </div>
  );
}
