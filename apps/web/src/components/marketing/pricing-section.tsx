"use client"

import { motion } from "framer-motion"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Check, Star } from "lucide-react"
import Link from "next/link"

const plans = [
  {
    name: "Free",
    price: "$0",
    period: "forever",
    description: "Perfect to get started",
    features: [
      "30 minutes of video processing/month",
      "5 clips generated",
      "Basic subtitle styles",
      "720p export quality",
      "Community support"
    ],
    cta: "Get Started",
    popular: false,
    href: "/sign-up"
  },
  {
    name: "Pro",
    price: "$19",
    period: "per month",
    description: "For serious creators",
    features: [
      "5 hours of video processing/month",
      "Unlimited clips",
      "All 5 premium subtitle styles",
      "1080p export quality",
      "Auto-posting to TikTok & Instagram",
      "Viral score analytics",
      "Priority processing",
      "Email support"
    ],
    cta: "Start Free Trial",
    popular: true,
    href: "/sign-up?plan=pro"
  },
  {
    name: "Team",
    price: "$49",
    period: "per month",
    description: "For agencies & teams",
    features: [
      "15 hours of video processing/month",
      "Unlimited clips",
      "All premium features",
      "4K export quality",
      "Team collaboration",
      "Brand kit customization",
      "Advanced analytics dashboard",
      "Custom subtitle styles",
      "Dedicated account manager",
      "Priority support"
    ],
    cta: "Contact Sales",
    popular: false,
    href: "/contact"
  }
]

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1
    }
  }
}

const itemVariants = {
  hidden: { opacity: 0, y: 60 },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.6,
      ease: "easeOut"
    }
  }
}

export function PricingSection() {
  return (
    <section className="py-24 bg-background" id="pricing">
      <div className="section-container">
        <motion.div
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-100px" }}
          variants={containerVariants}
          className="space-y-16"
        >
          {/* Header */}
          <motion.div variants={itemVariants} className="text-center space-y-4">
            <h2 className="text-3xl md:text-4xl lg:text-5xl font-bold text-white">
              Simple, Transparent Pricing
            </h2>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              Choose the perfect plan for your content creation needs. Start free, scale as you grow.
            </p>
          </motion.div>

          {/* Pricing Grid */}
          <motion.div
            variants={containerVariants}
            className="grid grid-cols-1 md:grid-cols-3 gap-8 lg:gap-12"
          >
            {plans.map((plan, index) => (
              <motion.div
                key={plan.name}
                variants={itemVariants}
                className="relative"
              >
                {/* Popular Badge */}
                {plan.popular && (
                  <div className="absolute -top-4 left-1/2 transform -translate-x-1/2 z-10">
                    <Badge className="bg-gradient-to-r from-pink-500 to-red-500 text-white border-0 px-4 py-1">
                      <Star className="w-3 h-3 mr-1" />
                      Most Popular
                    </Badge>
                  </div>
                )}

                {/* Plan Card */}
                <div className={`relative bg-card/50 backdrop-blur-sm rounded-2xl p-8 border transition-all duration-300 h-full ${
                  plan.popular
                    ? 'border-primary shadow-xl shadow-primary/20 bg-card/80'
                    : 'border-border hover:bg-card/80 hover:border-primary/20'
                }`}>
                  {/* Plan Header */}
                  <div className="space-y-4">
                    <div>
                      <h3 className="text-xl font-semibold text-white">
                        {plan.name}
                      </h3>
                      <p className="text-muted-foreground text-sm">
                        {plan.description}
                      </p>
                    </div>

                    {/* Price */}
                    <div className="flex items-baseline space-x-2">
                      <span className="text-4xl font-bold text-white">
                        {plan.price}
                      </span>
                      <span className="text-muted-foreground">
                        {plan.period}
                      </span>
                    </div>
                  </div>

                  {/* Features */}
                  <div className="space-y-4 my-8">
                    <ul className="space-y-3">
                      {plan.features.map((feature, featureIndex) => (
                        <li key={featureIndex} className="flex items-start space-x-3">
                          <Check className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" />
                          <span className="text-muted-foreground text-sm">
                            {feature}
                          </span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* CTA Button */}
                  <Button
                    asChild
                    className={`w-full ${
                      plan.popular
                        ? 'cta-button'
                        : 'bg-card border-border text-white hover:bg-card/80'
                    }`}
                    size="lg"
                  >
                    <Link href={plan.href}>
                      {plan.cta}
                    </Link>
                  </Button>

                  {/* Gradient overlay for popular plan */}
                  {plan.popular && (
                    <div className="absolute inset-0 bg-gradient-to-r from-pink-500/5 to-red-500/5 rounded-2xl pointer-events-none" />
                  )}
                </div>
              </motion.div>
            ))}
          </motion.div>

          {/* Bottom Note */}
          <motion.div variants={itemVariants} className="text-center space-y-4">
            <p className="text-muted-foreground">
              All plans include a 7-day free trial. No credit card required.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
              <p className="text-sm text-muted-foreground">
                Need something custom?
              </p>
              <Button variant="outline" size="sm" asChild>
                <Link href="/contact">
                  Contact Sales
                </Link>
              </Button>
            </div>
          </motion.div>
        </motion.div>
      </div>
    </section>
  )
}