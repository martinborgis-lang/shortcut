import './globals.css'
import type { Metadata, Viewport } from 'next'
// Temporarily disabled Google Fonts due to network issues
// import { Inter } from 'next/font/google'
import { ClerkProvider } from '@clerk/nextjs'
import { QueryProvider } from '@/lib/query-provider'

// const inter = Inter({
//   subsets: ['latin'],
//   display: 'swap',
//   preload: true
// })

export const metadata: Metadata = {
  title: 'ShortCut - AI Video Clip Creator',
  description: 'Transform long-form videos into viral TikTok clips with AI',
  icons: {
    icon: '/favicon.svg',
    shortcut: '/favicon.svg',
    apple: '/favicon.svg',
  },
  manifest: '/manifest.json',
}

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 5,
  themeColor: '#e94560',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <ClerkProvider>
      <html lang="en">
        <body className="font-sans">
          <QueryProvider>
            {children}
          </QueryProvider>
        </body>
      </html>
    </ClerkProvider>
  )
}