/**
 * Behavior (plan 012, D39): components draw color only from the tokens. No
 * .tsx file under app/ or components/ (tests excluded) may contain a hex
 * color, an rgb()/rgba()/hsl()/hsla() color, or a Tailwind palette utility
 * such as text-white, bg-black/10 or border-red-500. The one allowlisted use
 * is the viewport theme color in app/layout.tsx, which the browser reads
 * before any CSS loads, so it cannot be a token.
 */
import { readdirSync, readFileSync, statSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";

const ROOT = path.resolve(__dirname, "../..");
const DIRS = ["app", "components"];

const PALETTE =
  "black|white|slate|gray|zinc|neutral|stone|red|orange|amber|yellow|lime|green|emerald|teal|cyan|sky|blue|indigo|violet|purple|fuchsia|pink|rose";
const UTILITIES =
  "bg|text|border|border-[trblxy]|ring|ring-offset|outline|fill|stroke|from|via|to|decoration|divide|shadow|accent|caret|placeholder";

const PATTERNS: [string, RegExp][] = [
  ["hex color", /(?<![\w&])#(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{3,4})\b/g],
  ["rgb/hsl color", /(?<![a-zA-Z])(?:rgba?|hsla?)\(/g],
  ["palette utility", new RegExp(`(?<![\\w-])(?:${UTILITIES})-(?:${PALETTE})(?:-\\d{2,3})?(?:\\/\\d+)?(?![\\w-])`, "g")],
];

/** The viewport theme color in app/layout.tsx: a themeColor line or a color entry of it. */
function allowed(file: string, line: string): boolean {
  return file === "app/layout.tsx" && /\bthemeColor\b|\bcolor:\s*"#/.test(line);
}

function tsxFiles(dir: string): string[] {
  return readdirSync(dir).flatMap((name) => {
    const full = path.join(dir, name);
    if (statSync(full).isDirectory()) return tsxFiles(full);
    return name.endsWith(".tsx") && !name.endsWith(".test.tsx") ? [full] : [];
  });
}

function scan(): string[] {
  const hits: string[] = [];
  for (const dir of DIRS) {
    for (const full of tsxFiles(path.join(ROOT, dir))) {
      const file = path.relative(ROOT, full);
      readFileSync(full, "utf8")
        .split("\n")
        .forEach((line, i) => {
          if (allowed(file, line)) return;
          for (const [kind, re] of PATTERNS) {
            for (const m of line.matchAll(re)) hits.push(`${file}:${i + 1} ${kind} ${m[0]}`);
          }
        });
    }
  }
  return hits;
}

describe("no hardcoded colors", () => {
  it("the patterns catch what they should and leave the rest", () => {
    const hit = (s: string) => PATTERNS.some(([, re]) => new RegExp(re.source, "g").test(s));
    for (const s of ['fill="#2f3a8f"', "text-white", "bg-black/10", "border-red-500", "shadow-[0_0_rgb(0_0_0/0.3)]", "hsl(10 20% 30%)"]) {
      expect(hit(s), s).toBe(true);
    }
    for (const s of ["href={`#unit-${id}`}", "&#39;", "text-primary-foreground", "bg-accent/60", "text-danger", "whitespace-nowrap", "bg-desk"]) {
      expect(hit(s), s).toBe(false);
    }
  });

  it("finds none in app/ and components/", () => {
    expect(scan()).toEqual([]);
  });
});
