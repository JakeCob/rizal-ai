/**
 * Behaviors (plan 012, D39):
 * - the color math is right: known sRGB conversions, contrast of black on
 *   white is 21, composite blends, an out-of-gamut oklch throws
 * - parseTokens reads both dark shapes (a .dark block and a
 *   prefers-color-scheme media block) as an overlay on the merged :root set
 * - in app/globals.css, every named text pair reaches 4.5:1 and every named
 *   non-text pair 3:1, in light and in dark
 * - every light color token has a dark value and vice versa
 * - every --color-* mapping in the @theme blocks resolves in both schemes to
 *   a color inside the sRGB gamut
 *
 * A pair whose token does not exist yet fails with the contrast of what the
 * UI draws there today (for example white text on the success button), so a
 * red run reads as the list of fixes.
 */
import { readFileSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";
import {
  composite,
  contrast,
  isColorValue,
  oklchToSrgb,
  parseTokens,
  resolveValue,
  toRgba,
  type Rgb,
  type Tokens,
} from "./contrast";

const CSS = readFileSync(path.resolve(__dirname, "../../app/globals.css"), "utf8");
const TOKENS = parseTokens(CSS);
type Scheme = "light" | "dark";

/** What the UI draws today where a planned token does not exist yet. */
const TODAY: Record<string, string> = {
  "on-success": "white", // text-white on the success button (Runner.tsx)
  "on-danger": "white", // text-white on the danger button (Runner.tsx)
  gold: "var(--accent-foreground)", // XP and streak text use accent-foreground
  "primary-text": "var(--primary)", // text-primary on links and the play button
  progress: "var(--primary)", // the progress indicator is bg-primary
  highlight: "var(--accent)", // the quoted span is bg-accent/60 (drawn opaque here)
  "highlight-foreground": "var(--accent-foreground)",
};

function tokenColor(name: string, scheme: Scheme, tokens: Tokens = TOKENS) {
  const map = tokens[scheme];
  const raw = map.get(name);
  if (raw !== undefined) return toRgba(resolveValue(raw, map));
  const today = TODAY[name];
  const err = new Error(`--${name} is not defined in ${scheme}`) as Error & { today?: string };
  if (today) err.today = today;
  throw err;
}

/** "token" or "token@alpha"; an alpha (or a token's own alpha) composites over `base`. */
function refColor(ref: string, scheme: Scheme, base: Rgb): Rgb {
  const [name, alphaText] = ref.split("@");
  const c = tokenColor(name, scheme);
  const alpha = (alphaText === undefined ? 1 : Number(alphaText)) * c.a;
  return alpha >= 1 ? c : composite(c, alpha, base);
}

function pairRatio(fg: string, bg: string, scheme: Scheme): number {
  const page = tokenColor("background", scheme);
  const back = refColor(bg, scheme, page);
  return contrast(refColor(fg, scheme, back), back);
}

/** The ratio with today's stand-ins, for the failure message of a missing token. */
function todayRatio(fg: string, bg: string, scheme: Scheme): string {
  const withToday: Tokens = { ...TOKENS, [scheme]: new Map(TOKENS[scheme]) };
  for (const [name, value] of Object.entries(TODAY)) {
    if (!withToday[scheme].has(name)) withToday[scheme].set(name, value);
  }
  const color = (ref: string, base: Rgb) => {
    const [name, alphaText] = ref.split("@");
    const c = tokenColor(name, scheme, withToday);
    const alpha = (alphaText === undefined ? 1 : Number(alphaText)) * c.a;
    return alpha >= 1 ? c : composite(c, alpha, base);
  };
  const back = color(bg, tokenColor("background", scheme, withToday));
  return contrast(color(fg, back), back).toFixed(2);
}

const TEXT = 4.5;
const NON_TEXT = 3;

/** [foreground, background, minimum, only in this scheme] per the plan 012 map. */
const PAIRS: [string, string, number, Scheme?][] = [
  ["foreground", "background", TEXT],
  ["foreground", "card", TEXT],
  ["foreground", "popover", TEXT],
  ["primary-foreground", "primary", TEXT],
  ["primary-foreground@0.9", "primary", TEXT], // the unit label at opacity-90 on the banner
  ["muted-foreground", "background", TEXT],
  ["muted-foreground", "card", TEXT],
  ["muted-foreground", "muted", TEXT],
  ["muted-foreground", "popover", TEXT],
  ["muted-foreground", "danger@0.15", TEXT], // the explanation on the wrong sheet
  ["gold", "background", TEXT], // XP and streak text
  ["gold", "card", TEXT],
  ["highlight-foreground", "highlight", TEXT], // Rizal's quoted span
  ["success-foreground", "success@0.15", TEXT], // the correct sheet
  ["danger-foreground", "danger@0.15", TEXT], // the wrong sheet
  ["foreground", "success@0.15", TEXT],
  ["foreground", "danger@0.15", TEXT],
  ["on-success", "success", TEXT], // Continue on the correct sheet
  ["on-danger", "danger", TEXT], // Continue on the wrong sheet
  ["danger", "background", TEXT], // hearts and error text
  ["danger-foreground", "background", TEXT],
  ["primary-text", "background", TEXT], // text links, the current unit, the play icon
  ["accent-foreground", "accent", NON_TEXT], // the done node's check
  ["primary", "background", NON_TEXT], // the active node and buttons
  ["accent-lip", "background", NON_TEXT],
  ["ring", "background", NON_TEXT], // focus rings
  ["accent", "primary", NON_TEXT], // the sun on the active node
  ["progress", "muted", NON_TEXT], // progress fill on its track
  ["primary-text", "primary@0.1", NON_TEXT], // the chosen option's tint (ExerciseView)
  ["foreground", "primary-tint", TEXT], // the "Up next" and "In Rizal's voice" cards
  ["muted-foreground", "primary-tint", TEXT],
  ["primary-text", "primary-tint", TEXT], // the current unit's title, the play icon
  ["accent@0.6", "background", NON_TEXT, "dark"], // the active node's halo in dark
];

describe("color math", () => {
  it("converts oklch to sRGB", () => {
    const white = oklchToSrgb("oklch(1 0 0)");
    expect(white.r).toBeCloseTo(1, 3);
    expect(white.b).toBeCloseTo(1, 3);
    const black = oklchToSrgb("oklch(0 0 0)");
    expect(black.g).toBeCloseTo(0, 5);
    // #0038a8, the flag blue, is oklch(0.396 0.186 262.2)
    const blue = oklchToSrgb("oklch(0.396 0.186 262.2)");
    expect(blue.r * 255).toBeCloseTo(0, -1);
    expect(blue.g * 255).toBeCloseTo(0x38, -1);
    expect(blue.b * 255).toBeCloseTo(0xa8, -1);
    expect(oklchToSrgb("oklch(0.21 0.035 262 / 12%)").a).toBeCloseTo(0.12, 5);
  });

  it("throws on a color outside the sRGB gamut, within half an 8-bit step", () => {
    expect(() => oklchToSrgb("oklch(0.9 0.3 140)")).toThrow(/gamut/);
    expect(() => oklchToSrgb("oklch(0.995 0.006 85)")).not.toThrow(); // red 1.001 before clipping
  });

  it("computes WCAG contrast and blends tints", () => {
    const white = toRgba("#fff");
    const black = toRgba("#000");
    expect(contrast(black, white)).toBeCloseTo(21, 5);
    expect(contrast(white, white)).toBeCloseTo(1, 5);
    const grey = composite(black, 0.5, white);
    expect(grey.r).toBeCloseTo(0.5, 5);
  });
});

describe("parseTokens", () => {
  it("merges :root blocks in order and overlays a .dark block", () => {
    const t = parseTokens(":root{--a:#fff;--b:#000}:root{--a:#eee}.dark{--a:#111}");
    expect(t.light.get("a")).toBe("#eee");
    expect(t.dark.get("a")).toBe("#111");
    expect(t.dark.get("b")).toBe("#000");
    expect([...t.darkDeclared]).toEqual(["a"]);
  });

  it("overlays a prefers-color-scheme dark media block and reads @theme colors", () => {
    const t = parseTokens(
      "@import 'x';:root{--a:#fff}@media (prefers-color-scheme: dark){:root{--a:#111}}@theme inline{--color-a:var(--a);--font-x:serif}",
    );
    expect(t.dark.get("a")).toBe("#111");
    expect(t.themeColors.get("color-a")).toBe("var(--a)");
    expect(t.themeColors.has("font-x")).toBe(false);
  });

  it("ignores a media block that is not the dark scheme, and comments", () => {
    const t = parseTokens(":root{--a:#fff}/* :root{--a:#000} */@media (min-width: 48rem){:root{--a:#123}}");
    expect(t.light.get("a")).toBe("#fff");
    expect(t.dark.get("a")).toBe("#fff");
  });
});

describe.each(["light", "dark"] as const)("globals.css contrast, %s", (scheme) => {
  it.each(PAIRS.filter((p) => !p[3] || p[3] === scheme))(`%s on %s is at least %s:1`, (fg, bg, min) => {
    let ratio: number;
    try {
      ratio = pairRatio(fg, bg, scheme);
    } catch (e) {
      const err = e as Error & { today?: string };
      if (err.today) throw new Error(`${err.message}; today the UI draws ${err.today} there: ${todayRatio(fg, bg, scheme)}:1`);
      throw e;
    }
    expect(Number(ratio.toFixed(2)), `${fg} on ${bg} in ${scheme}`).toBeGreaterThanOrEqual(min);
  });
});

describe("globals.css token coverage", () => {
  const colorTokens = (map: Map<string, string>) =>
    [...map.keys()].filter((k) => {
      try {
        return isColorValue(resolveValue(map.get(k) as string, map));
      } catch {
        return false;
      }
    });

  it("gives every light color token a dark value", () => {
    const missing = colorTokens(TOKENS.light).filter((k) => !TOKENS.darkDeclared.has(k));
    expect(missing).toEqual([]);
  });

  it("defines every dark token in light too", () => {
    const extra = [...TOKENS.darkDeclared].filter((k) => !TOKENS.light.has(k));
    expect(extra).toEqual([]);
  });

  it.each(["light", "dark"] as const)("resolves every --color-* mapping to an in-gamut color in %s", (scheme) => {
    const broken: string[] = [];
    for (const [name, value] of TOKENS.themeColors) {
      try {
        const resolved = resolveValue(value, TOKENS[scheme]);
        if (isColorValue(resolved)) toRgba(resolved);
      } catch (e) {
        broken.push(`--${name}: ${(e as Error).message}`);
      }
    }
    expect(broken).toEqual([]);
  });
});
