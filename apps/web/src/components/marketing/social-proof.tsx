"use client"

import { motion } from "framer-motion"
import { Star, Quote } from "lucide-react"

const testimonials = [
  {
    content: "ShortCut transformed my YouTube channel! I went from 10k to 500k followers in just 3 months. The AI finds the perfect moments every time.",
    author: "Sarah Chen",
    role: "Gaming Creator",
    followers: "500K TikTok",
    rating: 5,
    avatar: "SC"
  },
  {
    content: "As a busy entrepreneur, ShortCut saves me 20 hours per week. The clips it generates get 10x more views than my manual edits.",
    author: "Marcus Rivera",
    role: "Business Coach",
    followers: "1.2M Instagram",
    rating: 5,
    avatar: "MR"
  },
  {
    content: "The viral score feature is incredible. It predicted 3 of my videos would hit 1M+ views, and they all did! This tool is pure magic.",
    author: "Emma Thompson",
    role: "Lifestyle Influencer",
    followers: "800K TikTok",
    rating: 5,
    avatar: "ET"
  },
  {
    content: "I've tried every video editing tool out there. ShortCut is the only one that truly understands what makes content go viral. Game changer!",
    author: "David Park",
    role: "Tech Reviewer",
    followers: "2.1M YouTube",
    rating: 5,
    avatar: "DP"
  },
  {
    content: "The auto-subtitles and perfect cropping save me hours. My engagement rate increased by 300% since using ShortCut. Absolutely love it!",
    author: "Jessica Alba",
    role: "Fitness Creator",
    followers: "650K TikTok",
    rating: 5,
    avatar: "JA"
  },
  {
    content: "ShortCut's AI is scary good at picking viral moments. It finds clips I would never think of, and they consistently perform better than my picks.",
    author: "Alex Johnson",
    role: "Comedy Creator",
    followers: "900K TikTok",
    rating: 5,
    avatar: "AJ"
  }
]

const trustedBy = [
  { name: "TikTok", logo: "🎵" },
  { name: "YouTube", logo: "▶️" },
  { name: "Instagram", logo: "📷" },
  { name: "Creators", logo: "👥" }
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

export function SocialProofSection() {
  return (
    <section className="py-24 bg-card/10">
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
              Loved by 10,000+ Creators
            </h2>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              Join thousands of successful creators who trust ShortCut to grow their audience and create viral content.
            </p>
          </motion.div>

          {/* Trusted By */}
          <motion.div variants={itemVariants} className="text-center space-y-8">
            <p className="text-muted-foreground font-medium">
              Trusted by creators on every platform
            </p>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
              {trustedBy.map((platform) => (
                <div key={platform.name} className="flex items-center justify-center space-x-3">
                  <span className="text-2xl">{platform.logo}</span>
                  <span className="text-muted-foreground font-medium">{platform.name}</span>
                </div>
              ))}
            </div>
          </motion.div>

          {/* Testimonials Grid */}
          <motion.div
            variants={containerVariants}
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8"
          >
            {testimonials.map((testimonial, index) => (
              <motion.div
                key={index}
                variants={itemVariants}
                className="group"
              >
                <div className="bg-card/50 backdrop-blur-sm rounded-2xl p-6 border border-border hover:bg-card/80 hover:border-primary/20 transition-all duration-300 h-full relative">
                  {/* Quote Icon */}
                  <div className="absolute -top-3 -left-3 w-8 h-8 bg-gradient-to-r from-pink-500 to-red-500 rounded-full flex items-center justify-center">
                    <Quote className="w-4 h-4 text-white" />
                  </div>

                  <div className="space-y-4">
                    {/* Stars */}
                    <div className="flex space-x-1">
                      {[...Array(testimonial.rating)].map((_, i) => (
                        <Star key={i} className="w-4 h-4 fill-yellow-400 text-yellow-400" />
                      ))}
                    </div>

                    {/* Content */}
                    <blockquote className="text-white leading-relaxed">
                      "{testimonial.content}"
                    </blockquote>

                    {/* Author */}
                    <div className="flex items-center space-x-3 pt-4 border-t border-border/50">
                      <div className="w-10 h-10 bg-gradient-to-r from-pink-500 to-red-500 rounded-full flex items-center justify-center text-white font-semibold text-sm">
                        {testimonial.avatar}
                      </div>
                      <div>
                        <div className="text-white font-medium">
                          {testimonial.author}
                        </div>
                        <div className="text-muted-foreground text-sm">
                          {testimonial.role} • {testimonial.followers}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Hover gradient effect */}
                  <div className="absolute inset-0 bg-gradient-to-r from-pink-500/5 to-red-500/5 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none" />
                </div>
              </motion.div>
            ))}
          </motion.div>

          {/* Stats */}
          <motion.div
            variants={itemVariants}
            className="grid grid-cols-2 md:grid-cols-4 gap-8 pt-16"
          >
            <div className="text-center space-y-2">
              <div className="text-3xl font-bold text-white">10,000+</div>
              <div className="text-muted-foreground">Happy Creators</div>
            </div>
            <div className="text-center space-y-2">
              <div className="text-3xl font-bold text-white">2M+</div>
              <div className="text-muted-foreground">Clips Generated</div>
            </div>
            <div className="text-center space-y-2">
              <div className="text-3xl font-bold text-white">50M+</div>
              <div className="text-muted-foreground">Total Views</div>
            </div>
            <div className="text-center space-y-2">
              <div className="text-3xl font-bold text-white">94%</div>
              <div className="text-muted-foreground">Success Rate</div>
            </div>
          </motion.div>
        </motion.div>
      </div>
    </section>
  )
}