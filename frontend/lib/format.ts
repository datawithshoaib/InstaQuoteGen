export function timeAgo(iso: string): string {
  const seconds = Math.max(1, Math.round((Date.now() - new Date(iso).getTime()) / 1000));
  const units: [number, string][] = [
    [60 * 60 * 24 * 30, "mo"],
    [60 * 60 * 24, "d"],
    [60 * 60, "h"],
    [60, "m"],
  ];
  for (const [size, label] of units) if (seconds >= size) return `${Math.floor(seconds / size)}${label} ago`;
  return "just now";
}

export const ms = (value: number | null | undefined) =>
  value == null ? "–" : value >= 1000 ? `${(value / 1000).toFixed(1)}s` : `${Math.round(value)}ms`;

export const compact = (value: number | null | undefined) =>
  value == null ? "–" : new Intl.NumberFormat("en", { notation: "compact" }).format(value);

export const pct = (value: number | null | undefined) => (value == null ? "–" : `${Math.round(value * 100)}%`);

/** Build a link that opens a quote in the studio. */
export function studioHref(q: { text: string; author?: string | null; keywords?: string[]; hashtags?: string[]; reflection?: string | null }) {
  const params = new URLSearchParams({ text: q.text });
  if (q.author) params.set("author", q.author);
  if (q.keywords?.length) params.set("keywords", q.keywords.join(","));
  if (q.hashtags?.length) params.set("hashtags", q.hashtags.join(","));
  if (q.reflection) params.set("reflection", q.reflection);
  return `/studio?${params.toString()}`;
}
