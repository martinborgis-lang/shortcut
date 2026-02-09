"use client"

import { motion } from "framer-motion"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Home, Search, ArrowLeft } from "lucide-react"

export default function NotFoundPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center">
      <div className="section-container">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="text-center space-y-8"
        >
          {/* 404 Animation */}
          <motion.div
            initial={{ scale: 0.5, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="relative"
          >
            <div className="text-8xl md:text-9xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-pink-500 to-red-500">
              404
            </div>
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
              className="absolute inset-0 opacity-20"
            >
              <div className="w-full h-full border-4 border-dashed border-pink-500 rounded-full" />
            </motion.div>
          </motion.div>

          {/* Content */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.4 }}
            className="space-y-6"
          >
            <h1 className="text-3xl md:text-4xl font-bold text-white">
              Page Not Found
            </h1>
            <p className="text-lg text-muted-foreground max-w-md mx-auto">
              Oops! The page you're looking for seems to have gone viral and disappeared.
              Let's get you back on track.
            </p>
          </motion.div>

          {/* Actions */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.6 }}
            className="flex flex-col sm:flex-row gap-4 justify-center items-center"
          >
            <Button size="lg" className="cta-button" asChild>
              <Link href="/">
                <Home className="mr-2 h-5 w-5" />
                Go Home
              </Link>
            </Button>

            <Button
              variant="outline"
              size="lg"
              className="border-border bg-card/50 backdrop-blur-sm"
              onClick={() => window.history.back()}
            >
              <ArrowLeft className="mr-2 h-5 w-5" />
              Go Back
            </Button>
          </motion.div>

          {/* Popular Links */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.8 }}
            className="pt-8"
          >
            <div className="space-y-4">
              <p className="text-muted-foreground">
                Or try one of these popular pages:
              </p>
              <div className="flex flex-wrap gap-4 justify-center">
                <Link
                  href="#features"
                  className="text-pink-400 hover:text-pink-300 transition-colors underline"
                >
                  Features
                </Link>
                <Link
                  href="#pricing"
                  className="text-pink-400 hover:text-pink-300 transition-colors underline"
                >
                  Pricing
                </Link>
                <Link
                  href="#faq"
                  className="text-pink-400 hover:text-pink-300 transition-colors underline"
                >
                  FAQ
                </Link>
                <Link
                  href="/sign-up"
                  className="text-pink-400 hover:text-pink-300 transition-colors underline"
                >
                  Get Started
                </Link>
              </div>
            </div>
          </motion.div>

          {/* Floating Elements */}
          <div className="absolute inset-0 pointer-events-none">
            <motion.div
              animate={{
                x: [0, 100, 0],
                y: [0, -100, 0],
              }}
              transition={{
                duration: 10,
                repeat: Infinity,
                ease: "easeInOut"
              }}
              className="absolute top-1/4 left-1/4 w-4 h-4 bg-pink-500 rounded-full opacity-30"
            />
            <motion.div
              animate={{
                x: [0, -100, 0],
                y: [0, 100, 0],
              }}
              transition={{
                duration: 12,
                repeat: Infinity,
                ease: "easeInOut"
              }}
              className="absolute top-3/4 right-1/4 w-6 h-6 bg-purple-500 rounded-full opacity-20"
            />
            <motion.div
              animate={{
                x: [0, 50, 0],
                y: [0, -50, 0],
              }}
              transition={{
                duration: 8,
                repeat: Infinity,
                ease: "easeInOut"
              }}
              className="absolute top-1/2 right-1/3 w-3 h-3 bg-red-500 rounded-full opacity-40"
            />
          </div>
        </motion.div>
      </div>
    </div>
  )
}