/**
 * Behaviors (plan 012, D39): the web app manifest carries the new palette
 * and a maskable icon.
 * - theme_color is the light --primary and background_color the light
 *   --background, both as hex (within one 8-bit step of the tokens)
 * - the icons include the SVG, the 192 and 512 PNGs, and a maskable 512,
 *   and every listed file exists, in public/ or as a Next metadata file in
 *   app/ (app/icon.svg serves /icon.svg; a public/icon.svg would clash with it)
 */
import { existsSync, readFileSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";
import { parseTokens, resolveValue, toRgba } from "./contrast";

const WEB = path.resolve(__dirname, "../..");
const manifest = JSON.parse(readFileSync(path.join(WEB, "public/manifest.json"), "utf8")) as {
  theme_color: string;
  background_color: string;
  icons: { src: string; sizes: string; type: string; purpose?: string }[];
};
const tokens = parseTokens(readFileSync(path.join(WEB, "app/globals.css"), "utf8"));

function tokenRgb255(name: string) {
  const c = toRgba(resolveValue(tokens.light.get(name) as string, tokens.light));
  return [c.r, c.g, c.b].map((v) => v * 255);
}

function hexRgb255(hex: string) {
  return [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16));
}

describe("manifest.json", () => {
  it.each([
    ["theme_color", "primary"],
    ["background_color", "background"],
  ] as const)("%s matches the light --%s", (key, token) => {
    const hex = manifest[key];
    expect(hex).toMatch(/^#[0-9a-f]{6}$/i);
    const want = tokenRgb255(token);
    hexRgb255(hex).forEach((v, i) => expect(Math.abs(v - want[i])).toBeLessThanOrEqual(1));
  });

  it("lists the svg, the 192 and 512 PNGs and a maskable 512, all present", () => {
    const find = (sizes: string, purpose?: string) =>
      manifest.icons.find((i) => i.sizes === sizes && (purpose ? i.purpose === purpose : i.purpose !== "maskable"));
    expect(manifest.icons.find((i) => i.type === "image/svg+xml")).toBeDefined();
    expect(find("192x192")).toBeDefined();
    expect(find("512x512")).toBeDefined();
    expect(find("512x512", "maskable")).toBeDefined();
    for (const icon of manifest.icons) {
      const served = existsSync(path.join(WEB, "public", icon.src)) || existsSync(path.join(WEB, "app", icon.src));
      expect(served, icon.src).toBe(true);
    }
  });
});
