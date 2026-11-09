import type { Metadata, Viewport } from "next";
import { Geist, Geist_Mono, Noto_Serif } from "next/font/google";
import { AuroraBackground } from "@/components/layout/aurora-background";
import { Providers } from "@/components/layout/providers";
import { SiteHeader } from "@/components/layout/site-header";
import "./globals.css";

const sans = Geist({ variable: "--font-sans", subsets: ["latin"] });
const mono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] });
// Same family as the font the backend renders posts with, so previews match exports.
const serif = Noto_Serif({ variable: "--font-serif", subsets: ["latin"], style: ["italic"], weight: ["400"] });

export const metadata: Metadata = {
  title: { default: "InstaQuote Studio", template: "%s · InstaQuote Studio" },
  description: "Write, review and design Instagram quote posts with an AI pipeline you can actually see.",
};

export const viewport: Viewport = { themeColor: "#14121c", colorScheme: "dark" };

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`dark ${sans.variable} ${mono.variable} ${serif.variable} antialiased`}>
      <body className="min-h-dvh overflow-x-clip">
        <Providers>
          <AuroraBackground />
          <SiteHeader />
          <main className="mx-auto w-full max-w-7xl px-4 pt-8 pb-24 sm:px-6">{children}</main>
        </Providers>
      </body>
    </html>
  );
}
