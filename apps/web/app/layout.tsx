import type { Metadata, Viewport } from "next";
import { Nunito, Source_Serif_4 } from "next/font/google";
import "./globals.css";
import { RegisterServiceWorker } from "@/components/pwa/RegisterServiceWorker";
import { Providers } from "./providers";

// Nunito for UI and modern Tagalog, a serif for historical passage layers
// (DECISIONS.md D28). Both are Open Font License.
const nunito = Nunito({
  variable: "--font-sans",
  subsets: ["latin", "latin-ext"],
  weight: ["400", "600", "700", "800"],
  display: "swap",
});

const sourceSerif = Source_Serif_4({
  variable: "--font-serif",
  subsets: ["latin", "latin-ext"],
  weight: ["400", "600"],
  style: ["normal", "italic"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "RizalAI",
  description: "Learn Tagalog through the world of Jose Rizal.",
  manifest: "/manifest.json",
  appleWebApp: { capable: true, statusBarStyle: "default", title: "RizalAI" },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
  // The browser chrome follows the system scheme (plan 012, D39): the flag
  // blue in light, the navy page in dark. Hex, because the browser reads it
  // before any CSS loads (allowlisted in lib/theme/no-hardcoded-colors.test.ts).
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#03379a" },
    { media: "(prefers-color-scheme: dark)", color: "#0b152a" },
  ],
  colorScheme: "light dark",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={`${nunito.variable} ${sourceSerif.variable}`}>
      {/* Below md the classes are the phone layout, unchanged. From md up the
          column becomes a framed card on the desk background (plan 009), a
          720px reading column (plan 010, D38). A page that sets
          data-layout="wide" on its root widens the frame for its own columns.
          From xl (1280px) the frame goes away (plan 011): the body takes the
          app background, the wrapper loses its border, corners and shadow,
          a wide page gets the full width (it caps itself), and every other
          page keeps the wrapper as its 720px reading column. */}
      <body className="min-h-dvh bg-background text-foreground antialiased md:bg-desk md:bg-banig md:px-6 md:py-8 xl:bg-background xl:bg-none xl:py-0">
        <Providers>
          <div
            data-app-column
            className="mx-auto flex min-h-dvh w-full max-w-md flex-col md:min-h-[calc(100dvh-4rem)] md:rounded-3xl md:border md:border-border md:bg-background md:shadow-xl md:max-w-(--frame-w) md:has-[[data-layout=wide]]:max-w-3xl lg:has-[[data-layout=wide]]:max-w-6xl xl:min-h-dvh xl:rounded-none xl:border-0 xl:[box-shadow:none] xl:has-[[data-layout=wide]]:max-w-none"
          >
            {children}
          </div>
        </Providers>
        <RegisterServiceWorker />
      </body>
    </html>
  );
}
