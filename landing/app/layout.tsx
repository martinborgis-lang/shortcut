import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "ShortCut - Transformez vos vidéos en shorts viraux grâce à l'IA",
  description: "ShortCut transforme vos vidéos YouTube et Twitch en clips prêts à poster sur TikTok, Reels et Shorts — en un clic. L'outil #1 de clipping IA pour créateurs.",
  keywords: "shorts, clips, IA, TikTok, YouTube, Twitch, Reels, viral, créateurs",
  authors: [{ name: "ShortCut" }],
  openGraph: {
    title: "ShortCut - Transformez vos vidéos en shorts viraux grâce à l'IA",
    description: "ShortCut transforme vos vidéos YouTube et Twitch en clips prêts à poster sur TikTok, Reels et Shorts — en un clic.",
    url: "https://shortcut.app",
    siteName: "ShortCut",
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "ShortCut - L'IA qui transforme vos vidéos en shorts viraux",
      },
    ],
    locale: "fr_FR",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "ShortCut - Transformez vos vidéos en shorts viraux grâce à l'IA",
    description: "ShortCut transforme vos vidéos YouTube et Twitch en clips prêts à poster sur TikTok, Reels et Shorts — en un clic.",
    images: ["/og-image.png"],
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      "max-video-preview": -1,
      "max-image-preview": "large",
      "max-snippet": -1,
    },
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="fr" className="scroll-smooth w-full overflow-x-hidden">
      <body className={`${inter.className} w-full overflow-x-hidden bg-zinc-950 text-white antialiased`}>
        {children}
      </body>
    </html>
  );
}