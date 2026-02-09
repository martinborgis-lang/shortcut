import { Metadata } from "next"
import { MarketingNavbar } from "@/components/marketing/navbar"
import { MarketingFooter } from "@/components/marketing/footer"
import { ErrorBoundary } from "@/components/shared/error-boundary"

export const metadata: Metadata = {
  title: "ShortCut - Turn Long Videos into Viral TikTok Shorts",
  description: "AI-powered video clipping that creates viral TikTok shorts from YouTube videos. Get millions of views with smart timing and professional subtitles.",
  keywords: ["AI video editing", "TikTok shorts", "YouTube clips", "viral videos", "auto subtitles", "video clipping", "content creation"],
  authors: [{ name: "ShortCut Team" }],
  creator: "ShortCut",
  publisher: "ShortCut",
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
  openGraph: {
    title: "ShortCut - AI Video Clipping for TikTok",
    description: "Turn any YouTube video into viral TikTok shorts with AI. Smart timing, perfect crops, and professional subtitles.",
    url: "https://shortcut.app",
    siteName: "ShortCut",
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "ShortCut - AI Video Clipping Platform"
      }
    ],
    locale: "en_US",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "ShortCut - AI Video Clipping",
    description: "Turn YouTube videos into viral TikToks with AI",
    images: ["/og-image.png"],
    creator: "@shortcutapp"
  },
  alternates: {
    canonical: "https://shortcut.app",
  },
  category: "technology",
}

export default function MarketingLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="min-h-screen bg-background">
      <MarketingNavbar />
      <ErrorBoundary>
        <main className="pt-16">
          {children}
        </main>
      </ErrorBoundary>
      <MarketingFooter />
    </div>
  )
}