"use client"

import Link from "next/link"
import { Zap, Twitter, Github, Linkedin } from "lucide-react"

export function MarketingFooter() {
  return (
    <footer className="bg-card border-t border-border">
      <div className="section-container py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {/* Brand */}
          <div className="space-y-4">
            <Link href="/" className="flex items-center space-x-2">
              <div className="p-2 bg-gradient-to-r from-pink-500 to-red-500 rounded-lg">
                <Zap className="h-5 w-5 text-white" />
              </div>
              <span className="text-xl font-bold text-white">ShortCut</span>
            </Link>
            <p className="text-muted-foreground text-sm">
              Turn long videos into viral TikTok shorts with AI-powered clipping.
            </p>
            <div className="flex space-x-4">
              <a href="https://twitter.com" className="text-muted-foreground hover:text-white transition-colors">
                <Twitter className="h-5 w-5" />
              </a>
              <a href="https://github.com" className="text-muted-foreground hover:text-white transition-colors">
                <Github className="h-5 w-5" />
              </a>
              <a href="https://linkedin.com" className="text-muted-foreground hover:text-white transition-colors">
                <Linkedin className="h-5 w-5" />
              </a>
            </div>
          </div>

          {/* Product */}
          <div className="space-y-4">
            <h4 className="text-white font-semibold">Product</h4>
            <ul className="space-y-2 text-sm">
              <li>
                <Link href="#features" className="text-muted-foreground hover:text-white transition-colors">
                  Features
                </Link>
              </li>
              <li>
                <Link href="#pricing" className="text-muted-foreground hover:text-white transition-colors">
                  Pricing
                </Link>
              </li>
              <li>
                <Link href="/sign-up" className="text-muted-foreground hover:text-white transition-colors">
                  Get Started
                </Link>
              </li>
              <li>
                <Link href="#faq" className="text-muted-foreground hover:text-white transition-colors">
                  FAQ
                </Link>
              </li>
            </ul>
          </div>

          {/* Company */}
          <div className="space-y-4">
            <h4 className="text-white font-semibold">Company</h4>
            <ul className="space-y-2 text-sm">
              <li>
                <Link href="/about" className="text-muted-foreground hover:text-white transition-colors">
                  About
                </Link>
              </li>
              <li>
                <Link href="/blog" className="text-muted-foreground hover:text-white transition-colors">
                  Blog
                </Link>
              </li>
              <li>
                <Link href="/careers" className="text-muted-foreground hover:text-white transition-colors">
                  Careers
                </Link>
              </li>
              <li>
                <Link href="/contact" className="text-muted-foreground hover:text-white transition-colors">
                  Contact
                </Link>
              </li>
            </ul>
          </div>

          {/* Legal */}
          <div className="space-y-4">
            <h4 className="text-white font-semibold">Legal</h4>
            <ul className="space-y-2 text-sm">
              <li>
                <Link href="/privacy" className="text-muted-foreground hover:text-white transition-colors">
                  Privacy Policy
                </Link>
              </li>
              <li>
                <Link href="/terms" className="text-muted-foreground hover:text-white transition-colors">
                  Terms of Service
                </Link>
              </li>
              <li>
                <Link href="/cookies" className="text-muted-foreground hover:text-white transition-colors">
                  Cookie Policy
                </Link>
              </li>
            </ul>
          </div>
        </div>

        <div className="mt-8 pt-8 border-t border-border flex flex-col md:flex-row justify-between items-center">
          <p className="text-muted-foreground text-sm">
            © 2024 ShortCut. All rights reserved.
          </p>
          <p className="text-muted-foreground text-sm mt-4 md:mt-0">
            Made with ❤️ for content creators
          </p>
        </div>
      </div>
    </footer>
  )
}