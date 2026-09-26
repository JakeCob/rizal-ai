/**
 * Color tokens and WCAG contrast, dependency-free (plan 012, D39).
 *
 * parseTokens reads app/globals.css the way the browser resolves it for the
 * two color schemes:
 * - light: every top-level `:root { ... }` block, merged in source order
 *   (later declarations win);
 * - dark: the light set overlaid with the dark declarations, in source
 *   order, from either shape the file may use: a top-level `.dark { ... }`
 *   block (the class variant, used until plan 012) or a `:root { ... }` rule
 *   inside `@media (prefers-color-scheme: dark) { ... }` (the system
 *   setting, from plan 012 on). Both shapes are read, so the same test is
 *   meaningful before and after the switch.
 * It also collects the `--color-*` mappings of every `@theme` block.
 *
 * The color math follows CSS Color 4 (OKLCH to OKLab to linear sRGB) and
 * WCAG 2.x (relative luminance and contrast ratio). Tints such as
 * `bg-danger/15` are composited in gamma-encoded sRGB, as browsers do.
 */

export type Tokens = {
  /** Resolved light values, name without the leading `--`. */
  light: Map<string, string>;
  /** Resolved dark values: light overlaid with the dark declarations. */
  dark: Map<string, string>;
  /** Names declared in a dark block (not inherited from light). */
  darkDeclared: Set<string>;
  /** `--color-*` names from `@theme` blocks mapped to their raw values. */
  themeColors: Map<string, string>;
};

export type Rgb = { r: number; g: number; b: number };
export type Rgba = Rgb & { a: number };

type Block = { prelude: string; body: string };

/** Top-level `prelude { body }` blocks of a stylesheet (comments removed). */
function blocks(css: string): Block[] {
  const out: Block[] = [];
  let depth = 0;
  let start = 0;
  let open = -1;
  for (let i = 0; i < css.length; i++) {
    const ch = css[i];
    if (ch === "{") {
      if (depth === 0) open = i;
      depth++;
    } else if (ch === "}") {
      depth--;
      if (depth === 0 && open >= 0) {
        out.push({ prelude: css.slice(start, open).trim(), body: css.slice(open + 1, i) });
        start = i + 1;
        open = -1;
      }
    } else if (ch === ";" && depth === 0) {
      start = i + 1; // a top-level statement such as @import or @custom-variant
    }
  }
  return out;
}

function declarations(body: string): [string, string][] {
  const out: [string, string][] = [];
  for (const part of body.split(";")) {
    const m = part.match(/^\s*--([\w-]+)\s*:\s*([\s\S]+?)\s*$/);
    if (m) out.push([m[1], m[2]]);
  }
  return out;
}

export function parseTokens(source: string): Tokens {
  const css = source.replace(/\/\*[\s\S]*?\*\//g, "");
  const light = new Map<string, string>();
  const darkOwn: [string, string][] = [];
  const themeColors = new Map<string, string>();

  for (const { prelude, body } of blocks(css)) {
    if (prelude === ":root") {
      for (const [k, v] of declarations(body)) light.set(k, v);
    } else if (prelude === ".dark") {
      darkOwn.push(...declarations(body));
    } else if (/^@media\b/.test(prelude) && /prefers-color-scheme\s*:\s*dark/.test(prelude)) {
      for (const inner of blocks(body)) {
        if (inner.prelude === ":root") darkOwn.push(...declarations(inner.body));
      }
    } else if (/^@theme\b/.test(prelude)) {
      for (const [k, v] of declarations(body)) if (k.startsWith("color-")) themeColors.set(k, v);
    }
  }

  const dark = new Map(light);
  for (const [k, v] of darkOwn) dark.set(k, v);
  return { light, dark, darkDeclared: new Set(darkOwn.map(([k]) => k)), themeColors };
}

/** True for values that are colors rather than lengths, urls or numbers. */
export function isColorValue(value: string): boolean {
  return /^(#|oklch\(|oklab\(|rgba?\(|hsla?\(|lab\(|lch\(|color\()/i.test(value.trim());
}

/** Follow `var(--x)` references (with no fallback) through a token map. */
export function resolveValue(value: string, tokens: Map<string, string>, seen: string[] = []): string {
  const m = value.trim().match(/^var\(\s*--([\w-]+)\s*\)$/);
  if (!m) return value.trim();
  const name = m[1];
  if (seen.includes(name)) throw new Error(`circular var(--${name})`);
  const next = tokens.get(name);
  if (next === undefined) throw new Error(`--${name} is not defined`);
  return resolveValue(next, tokens, [...seen, name]);
}

function num(part: string, percentScale: number): number {
  const p = part.trim();
  return p.endsWith("%") ? (parseFloat(p) / 100) * percentScale : parseFloat(p);
}

/**
 * How far a channel may fall outside 0 to 1, in gamma-encoded sRGB, before
 * the color counts as out of gamut: half an 8-bit step. Clipping a smaller
 * excursion changes no rendered 8-bit value, so hand-rounded tokens such as
 * oklch(0.995 0.006 85) (red channel 1.001 before clipping) pass, while a
 * color that clipping would visibly change throws.
 */
const GAMUT_TOLERANCE = 0.5 / 255;

/** The sRGB transfer function, extended to negative values and values over 1 by symmetry. */
function encode(c: number): number {
  const x = Math.abs(c);
  const e = x <= 0.0031308 ? 12.92 * x : 1.055 * x ** (1 / 2.4) - 0.055;
  return Math.sign(c) * e;
}

/**
 * An oklch() color to gamma-encoded sRGB (0 to 1) with alpha. Throws when
 * the color lies outside the sRGB gamut, where a browser would clip it and
 * the token would not render as written.
 */
export function oklchToSrgb(value: string): Rgba {
  const m = value.trim().match(/^oklch\(\s*([^\s/]+)\s+([^\s/]+)\s+([^\s/)]+)\s*(?:\/\s*([^\s)]+)\s*)?\)$/i);
  if (!m) throw new Error(`not an oklch() color: ${value}`);
  const L = num(m[1], 1);
  const C = num(m[2], 0.4);
  const H = (parseFloat(m[3]) * Math.PI) / 180;
  const alpha = m[4] === undefined ? 1 : num(m[4], 1);

  const a = C * Math.cos(H);
  const b = C * Math.sin(H);
  const l_ = L + 0.3963377774 * a + 0.2158037573 * b;
  const m_ = L - 0.1055613458 * a - 0.0638541728 * b;
  const s_ = L - 0.0894841775 * a - 1.291485548 * b;
  const l = l_ ** 3;
  const mm = m_ ** 3;
  const s = s_ ** 3;
  const lin = [
    4.0767416621 * l - 3.3077115913 * mm + 0.2309699292 * s,
    -1.2684380046 * l + 2.6097574011 * mm - 0.3413193965 * s,
    -0.0041960863 * l - 0.7034186147 * mm + 1.707614701 * s,
  ];
  const gamma = lin.map(encode);
  if (gamma.some((c) => c < -GAMUT_TOLERANCE || c > 1 + GAMUT_TOLERANCE)) {
    throw new Error(`${value} is outside the sRGB gamut (sRGB ${gamma.map((c) => c.toFixed(4)).join(", ")})`);
  }
  const [r, g, bl] = gamma.map((c) => Math.min(1, Math.max(0, c)));
  return { r, g, b: bl, a: alpha };
}

/** Any token value this app uses (oklch or hex) to sRGB with alpha. */
export function toRgba(value: string): Rgba {
  const v = value.trim();
  if (/^oklch\(/i.test(v)) return oklchToSrgb(v);
  const hex = v.match(/^#([0-9a-f]{3}|[0-9a-f]{6})$/i);
  if (hex) {
    const h = hex[1].length === 3 ? [...hex[1]].map((c) => c + c).join("") : hex[1];
    return { r: parseInt(h.slice(0, 2), 16) / 255, g: parseInt(h.slice(2, 4), 16) / 255, b: parseInt(h.slice(4, 6), 16) / 255, a: 1 };
  }
  if (v === "white") return { r: 1, g: 1, b: 1, a: 1 };
  if (v === "black") return { r: 0, g: 0, b: 0, a: 1 };
  throw new Error(`unsupported color value: ${value}`);
}

/** WCAG relative luminance of a gamma-encoded sRGB color. */
export function luminance({ r, g, b }: Rgb): number {
  const lin = (c: number) => (c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4);
  return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b);
}

/** WCAG contrast ratio, 1 to 21. */
export function contrast(a: Rgb, b: Rgb): number {
  const [hi, lo] = [luminance(a), luminance(b)].sort((x, y) => y - x);
  return (hi + 0.05) / (lo + 0.05);
}

/** A color at `alpha` over an opaque background, in gamma-encoded sRGB. */
export function composite(fg: Rgb, alpha: number, bg: Rgb): Rgb {
  return {
    r: fg.r * alpha + bg.r * (1 - alpha),
    g: fg.g * alpha + bg.g * (1 - alpha),
    b: fg.b * alpha + bg.b * (1 - alpha),
  };
}
