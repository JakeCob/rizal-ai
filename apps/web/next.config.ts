import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // The dev-tools badge overlays the page under `next dev` only, where the
  // layout gate and the screens spec would capture it (plan 012). Builds
  // never show it, so this changes nothing in production.
  devIndicators: false,
};

export default nextConfig;
