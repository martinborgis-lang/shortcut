"use client"

import { Metadata } from "next"
import { PricingSection } from "@/components/marketing/pricing-section"
import { FAQSection } from "@/components/marketing/faq-section"

const metadata: Metadata = {
  title: "Pricing - ShortCut",
  description: "Simple, transparent pricing for AI-powered video clipping. Start free and scale as you grow your content creation business.",
  keywords: ["video editing pricing", "AI video tools cost", "TikTok shorts pricing", "content creation tools"],
}

export default function PricingPage() {
  return (
    <div className="py-16 space-y-16">
      {/* Hero Section */}
      <section className="py-24 bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
        <div className="section-container text-center space-y-8">
          <div className="space-y-4">
            <h1 className="text-4xl md:text-6xl font-bold text-white">
              Simple, Transparent Pricing
            </h1>
            <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
              Choose the perfect plan for your content creation needs. Start free, upgrade when you're ready to scale your viral content strategy.
            </p>
          </div>

          {/* Trust indicators */}
          <div className="grid grid-cols-3 gap-8 max-w-md mx-auto pt-8">
            <div className="text-center">
              <div className="text-2xl font-bold text-white">7 days</div>
              <div className="text-sm text-muted-foreground">Free trial</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-white">No setup</div>
              <div className="text-sm text-muted-foreground">fees</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-white">Cancel</div>
              <div className="text-sm text-muted-foreground">anytime</div>
            </div>
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <PricingSection />

      {/* FAQ Section */}
      <FAQSection />

      {/* Bottom CTA */}
      <section className="py-16 bg-card/20">
        <div className="section-container text-center space-y-8">
          <h2 className="text-3xl font-bold text-white">
            Ready to Start Creating Viral Content?
          </h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Join thousands of successful creators who trust ShortCut to grow their audience and create engaging short-form content.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <button className="inline-flex items-center justify-center px-8 py-4 bg-gradient-to-r from-pink-500 to-red-500 hover:from-pink-600 hover:to-red-600 text-white font-semibold rounded-lg transition-all duration-300 shadow-lg hover:shadow-xl">
              Start Free Trial
            </button>
            <button className="inline-flex items-center justify-center px-8 py-4 bg-card border border-border text-white rounded-lg hover:bg-card/80 transition-colors duration-300">
              Schedule Demo
            </button>
          </div>
        </div>
      </section>
    </div>
  )
}