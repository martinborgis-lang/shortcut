"use client"

import { Metadata } from "next"
import Pricing from "@/components/landing/Pricing"
import FAQ from "@/components/landing/FAQ"
import Navbar from "@/components/landing/Navbar"
import Footer from "@/components/landing/Footer"

const metadata: Metadata = {
  title: "Pricing - ShortCut",
  description: "Simple, transparent pricing for AI-powered video clipping. Start free and scale as you grow your content creation business.",
  keywords: ["video editing pricing", "AI video tools cost", "TikTok shorts pricing", "content creation tools"],
}

export default function PricingPage() {
  return (
    <div className="w-full min-h-screen overflow-x-hidden bg-zinc-950 text-white">
      <Navbar />
      <main className="w-full">
        {/* Hero Section */}
        <section className="py-24 pt-32 bg-zinc-950 relative overflow-hidden">
          <div className="absolute inset-0">
            <div
              className="absolute inset-0 opacity-20"
              style={{
                backgroundImage: 'linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px)',
                backgroundSize: '60px 60px',
              }}
            />
            <div className="absolute inset-0 bg-gradient-to-br from-purple-600/20 via-transparent to-cyan-500/20" />
          </div>
          <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center space-y-8">
            <div className="space-y-4">
              <h1 className="text-4xl md:text-6xl font-bold text-white">
                Simple, Transparent Pricing
              </h1>
              <p className="text-xl text-gray-400 max-w-3xl mx-auto">
                Choose the perfect plan for your content creation needs. Start free, upgrade when you're ready to scale your viral content strategy.
              </p>
            </div>

            {/* Trust indicators */}
            <div className="grid grid-cols-3 gap-8 max-w-md mx-auto pt-8">
              <div className="text-center">
                <div className="text-2xl font-bold text-white">7 days</div>
                <div className="text-sm text-gray-400">Free trial</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-white">No setup</div>
                <div className="text-sm text-gray-400">fees</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-white">Cancel</div>
                <div className="text-sm text-gray-400">anytime</div>
              </div>
            </div>
          </div>
        </section>

        {/* Pricing Section */}
        <Pricing />

        {/* FAQ Section */}
        <FAQ />
      </main>
      <Footer />
    </div>
  )
}