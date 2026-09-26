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
  themeColor: "#2f3a8f",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={`${nunito.variable} ${sourceSerif.variable}`}>
      {/* Below md the classes are the phone layout, unchanged. From md up the
          column becomes a framed card on the desk background (plan 009). */}
      <body className="min-h-dvh bg-background text-foreground antialiased md:bg-desk md:py-8">
        <Providers>
          <div
            data-app-column
            className="mx-auto flex min-h-dvh w-full max-w-md flex-col md:min-h-[calc(100dvh-4rem)] md:rounded-3xl md:border md:border-border md:bg-background md:shadow-xl"
          >
            {children}
          </div>
        </Providers>
        <RegisterServiceWorker />
      </body>
    </html>
  );
}
