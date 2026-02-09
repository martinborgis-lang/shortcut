"use client"

import { HeroSection } from "@/components/marketing/hero-section"
import { HowItWorks } from "@/components/marketing/how-it-works"
import { FeaturesSection } from "@/components/marketing/features-section"
import { PricingSection } from "@/components/marketing/pricing-section"
import { SocialProofSection } from "@/components/marketing/social-proof"
import { FAQSection } from "@/components/marketing/faq-section"

export default function MarketingHomePage() {
  return (
    <div className="overflow-hidden">
      <HeroSection />
      <HowItWorks />
      <FeaturesSection />
      <SocialProofSection />
      <PricingSection />
      <FAQSection />
    </div>
  )
}