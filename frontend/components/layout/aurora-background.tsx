/**
 * Slow-moving colour fields behind every page, plus a grain layer.
 *
 * The soft glow comes from radial gradients rather than `filter: blur()`.
 * Huge blurred layers look the same but are very expensive to repaint,
 * especially on machines without GPU compositing.
 */
const blob = (color: string) => ({
  background: `radial-gradient(closest-side, ${color}, transparent)`,
  willChange: "transform",
});

export function AuroraBackground() {
  return (
    <div aria-hidden className="pointer-events-none fixed inset-0 -z-10 overflow-hidden">
      <div
        className="absolute -top-[25%] -left-[15%] size-[70vmax] animate-aurora"
        style={blob("color-mix(in oklch, var(--violet) 30%, transparent)")}
      />
      <div
        className="absolute top-[5%] -right-[20%] size-[60vmax] animate-aurora"
        style={{ ...blob("color-mix(in oklch, var(--gold) 18%, transparent)"), animationDelay: "-7s" }}
      />
      <div
        className="absolute -bottom-[30%] left-[15%] size-[65vmax] animate-aurora"
        style={{ ...blob("color-mix(in oklch, var(--teal) 14%, transparent)"), animationDelay: "-14s" }}
      />
      <div className="grain absolute inset-0 opacity-[0.06] mix-blend-overlay" />
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,transparent_0%,var(--background)_75%)]" />
    </div>
  );
}
