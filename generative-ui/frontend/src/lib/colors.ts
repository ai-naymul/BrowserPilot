/**
 * Color softening — keep the hue, calm the intensity.
 *
 * The render LLM is free to pick any series color for a chart (e.g. a vivid
 * "#3b82f6" or "#10b981"). Rather than constrain the model to a fixed palette
 * (which would fight the "generalized, LLM-decides" design), we soften whatever
 * it returns at the render edge: preserve the hue so blue stays blue and green
 * stays green, but lift the color into a soft, pastel range that matches the
 * glass theme. This is generalized — it works for ANY input color, no per-chart
 * or per-domain rules.
 */

function hexToRgb(hex: string): [number, number, number] | null {
  let h = hex.trim().replace(/^#/, "");
  if (h.length === 3) h = h.split("").map((c) => c + c).join("");
  if (h.length !== 6 || /[^0-9a-fA-F]/.test(h)) return null;
  const n = parseInt(h, 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}

function rgbToHsl(r: number, g: number, b: number): [number, number, number] {
  r /= 255; g /= 255; b /= 255;
  const max = Math.max(r, g, b);
  const min = Math.min(r, g, b);
  const d = max - min;
  let h = 0;
  const l = (max + min) / 2;
  const s = d === 0 ? 0 : d / (1 - Math.abs(2 * l - 1));
  if (d !== 0) {
    switch (max) {
      case r: h = ((g - b) / d) % 6; break;
      case g: h = (b - r) / d + 2; break;
      default: h = (r - g) / d + 4; break;
    }
    h *= 60;
    if (h < 0) h += 360;
  }
  return [h, s, l];
}

function hslToHex(h: number, s: number, l: number): string {
  const c = (1 - Math.abs(2 * l - 1)) * s;
  const x = c * (1 - Math.abs(((h / 60) % 2) - 1));
  const m = l - c / 2;
  let r = 0, g = 0, b = 0;
  if (h < 60) { r = c; g = x; }
  else if (h < 120) { r = x; g = c; }
  else if (h < 180) { g = c; b = x; }
  else if (h < 240) { g = x; b = c; }
  else if (h < 300) { r = x; b = c; }
  else { r = c; b = x; }
  const to = (v: number) => Math.round((v + m) * 255).toString(16).padStart(2, "0");
  return `#${to(r)}${to(g)}${to(b)}`;
}

/**
 * Return a softer, same-hue version of any color. Lifts lightness into the
 * pastel band (~0.74–0.82) and eases saturation, so vivid inputs become calm
 * without shifting the underlying color. Unparseable inputs pass through.
 */
export function soften(color: string | undefined | null): string | undefined {
  if (!color) return color ?? undefined;
  const rgb = hexToRgb(color);
  if (!rgb) return color; // named colors / hsl() / gradients — leave untouched
  const [h, s, l] = rgbToHsl(rgb[0], rgb[1], rgb[2]);
  const newL = Math.min(0.82, Math.max(l, 0.74));
  const newS = Math.min(s, 0.8);
  return hslToHex(h, newS, newL);
}
