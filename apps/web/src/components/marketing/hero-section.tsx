"use client"

import { motion } from "framer-motion"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { ArrowRight, Play } from "lucide-react"

export function HeroSection() {
  return (
    <section className="hero-section relative overflow-hidden">
      {/* Background gradient effects */}
      <div className="absolute inset-0 bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900" />
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(233,69,96,0.1)_0%,transparent_100%)]" />

      <div className="section-container relative z-10">
        <div className="text-center space-y-8">
          {/* Badge */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="inline-flex items-center px-4 py-2 rounded-full bg-card/50 border border-border backdrop-blur-sm"
          >
            <span className="text-sm text-muted-foreground">🚀 Join 10,000+ creators making viral content</span>
          </motion.div>

          {/* Headline */}
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="text-4xl md:text-6xl lg:text-7xl font-bold text-white leading-tight"
          >
            Turn Long Videos into{" "}
            <span className="text-gradient">Viral TikTok Shorts</span>
          </motion.h1>

          {/* Subtitle */}
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="text-lg md:text-xl text-muted-foreground max-w-3xl mx-auto leading-relaxed"
          >
            AI-powered video clips that get millions of views. Upload any YouTube video and get ready-to-post TikToks in minutes with perfect timing and professional subtitles.
          </motion.p>

          {/* CTA Buttons */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.4 }}
            className="flex flex-col sm:flex-row gap-4 justify-center items-center"
          >
            <Button size="lg" className="cta-button text-lg px-8 py-4" asChild>
              <Link href="/sign-up">
                Start for Free <ArrowRight className="ml-2 h-5 w-5" />
              </Link>
            </Button>
            <Button variant="outline" size="lg" className="text-lg px-8 py-4 border-border bg-card/50 backdrop-blur-sm" asChild>
              <Link href="#demo">
                <Play className="mr-2 h-5 w-5" />
                Watch Demo
              </Link>
            </Button>
          </motion.div>

          {/* Social Proof Numbers */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.5 }}
            className="grid grid-cols-3 gap-8 max-w-md mx-auto pt-8"
          >
            <div className="text-center">
              <div className="text-2xl md:text-3xl font-bold text-white">10K+</div>
              <div className="text-sm text-muted-foreground">Creators</div>
            </div>
            <div className="text-center">
              <div className="text-2xl md:text-3xl font-bold text-white">50M+</div>
              <div className="text-sm text-muted-foreground">Views Generated</div>
            </div>
            <div className="text-center">
              <div className="text-2xl md:text-3xl font-bold text-white">2M+</div>
              <div className="text-sm text-muted-foreground">Clips Created</div>
            </div>
          </motion.div>

          {/* Demo Video Placeholder */}
          <motion.div
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.6 }}
            className="mt-16"
          >
            <div className="relative max-w-4xl mx-auto">
              <div className="aspect-video bg-card/20 backdrop-blur-sm rounded-xl border border-border overflow-hidden">
                <div className="flex items-center justify-center h-full">
                  <div className="text-center space-y-4">
                    <div className="w-16 h-16 bg-gradient-to-r from-pink-500 to-red-500 rounded-full flex items-center justify-center mx-auto">
                      <Play className="h-8 w-8 text-white ml-1" />
                    </div>
                    <p className="text-muted-foreground">Demo video coming soon</p>
                  </div>
                </div>
              </div>
              {/* Floating elements */}
              <div className="absolute -top-4 -left-4 w-24 h-24 bg-gradient-to-r from-pink-500/20 to-red-500/20 rounded-full blur-xl animate-pulse" />
              <div className="absolute -bottom-4 -right-4 w-32 h-32 bg-gradient-to-r from-blue-500/20 to-purple-500/20 rounded-full blur-xl animate-pulse delay-75" />
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  )
}