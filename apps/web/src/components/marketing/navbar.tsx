"use client"

import { useState } from "react"
import Link from "next/link"
import { motion } from "framer-motion"
import { Button } from "@/components/ui/button"
import { Menu, X, Zap } from "lucide-react"

export function MarketingNavbar() {
  const [isOpen, setIsOpen] = useState(false)

  return (
    <motion.nav
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      transition={{ duration: 0.6, ease: "easeOut" }}
      className="fixed top-0 left-0 right-0 z-50 bg-background/80 backdrop-blur-md border-b border-border"
    >
      <div className="section-container">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center space-x-2">
            <div className="p-2 bg-gradient-to-r from-pink-500 to-red-500 rounded-lg">
              <Zap className="h-5 w-5 text-white" />
            </div>
            <span className="text-xl font-bold text-white">ShortCut</span>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-8">
            <Link href="#features" className="text-muted-foreground hover:text-white transition-colors">
              Features
            </Link>
            <Link href="#pricing" className="text-muted-foreground hover:text-white transition-colors">
              Pricing
            </Link>
            <Link href="#faq" className="text-muted-foreground hover:text-white transition-colors">
              FAQ
            </Link>
          </div>

          {/* Desktop CTA */}
          <div className="hidden md:flex items-center space-x-4">
            <Button variant="ghost" asChild>
              <Link href="/sign-in">Sign In</Link>
            </Button>
            <Button className="cta-button" asChild>
              <Link href="/sign-up">Get Started</Link>
            </Button>
          </div>

          {/* Mobile menu button */}
          <button
            onClick={() => setIsOpen(!isOpen)}
            className="md:hidden p-2 text-white"
          >
            {isOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
          </button>
        </div>

        {/* Mobile Navigation */}
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="md:hidden py-4 space-y-4 border-t border-border"
          >
            <Link href="#features" className="block text-muted-foreground hover:text-white transition-colors">
              Features
            </Link>
            <Link href="#pricing" className="block text-muted-foreground hover:text-white transition-colors">
              Pricing
            </Link>
            <Link href="#faq" className="block text-muted-foreground hover:text-white transition-colors">
              FAQ
            </Link>
            <div className="pt-4 space-y-2">
              <Button variant="ghost" className="w-full" asChild>
                <Link href="/sign-in">Sign In</Link>
              </Button>
              <Button className="cta-button w-full" asChild>
                <Link href="/sign-up">Get Started</Link>
              </Button>
            </div>
          </motion.div>
        )}
      </div>
    </motion.nav>
  )
}