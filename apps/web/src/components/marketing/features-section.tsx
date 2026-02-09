"use client"

import { motion } from "framer-motion"
import { Zap, Type, Calendar, BarChart3, Crop, Download, Clock, Users } from "lucide-react"

const features = [
  {
    icon: <Zap />,
    title: "AI-Powered Clipping",
    description: "Smart algorithms identify the most viral moments automatically using advanced machine learning trained on millions of viral videos"
  },
  {
    icon: <Type />,
    title: "Auto Subtitles",
    description: "5 professional subtitle styles that boost engagement by 80%. Choose from minimal, bold, gaming, and cinematic styles"
  },
  {
    icon: <Calendar />,
    title: "Smart Scheduling",
    description: "Publish across TikTok, Instagram, YouTube at optimal times based on your audience analytics and platform best practices"
  },
  {
    icon: <BarChart3 />,
    title: "Viral Score",
    description: "Each clip gets a viral prediction score based on proven engagement patterns, hook strength, and content quality"
  },
  {
    icon: <Crop />,
    title: "Perfect Crop",
    description: "Auto-crop to 9:16 with face detection for maximum impact. Smart framing keeps the focus on speakers and key visuals"
  },
  {
    icon: <Download />,
    title: "Instant Download",
    description: "High-quality MP4 exports ready for any platform. Batch download multiple clips with custom naming and folders"
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

export function FeaturesSection() {
  return (
    <section className="py-24 bg-card/20" id="features">
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
              Everything You Need to Go Viral
            </h2>
            <p className="text-lg text-muted-foreground max-w-3xl mx-auto">
              Powerful AI tools designed specifically for content creators. Create professional shorts that stand out and drive engagement.
            </p>
          </motion.div>

          {/* Features Grid */}
          <motion.div
            variants={containerVariants}
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8"
          >
            {features.map((feature, index) => (
              <motion.div
                key={feature.title}
                variants={itemVariants}
                className="group relative"
              >
                <div className="bg-card/50 backdrop-blur-sm rounded-2xl p-8 border border-border hover:bg-card/80 hover:border-primary/20 transition-all duration-300 h-full">
                  {/* Icon */}
                  <div className="w-14 h-14 bg-gradient-to-r from-pink-500 to-red-500 rounded-xl flex items-center justify-center text-white mb-6 group-hover:scale-110 group-hover:rotate-3 transition-transform duration-300">
                    {feature.icon}
                  </div>

                  {/* Content */}
                  <div className="space-y-4">
                    <h3 className="text-xl font-semibold text-white">
                      {feature.title}
                    </h3>
                    <p className="text-muted-foreground leading-relaxed">
                      {feature.description}
                    </p>
                  </div>

                  {/* Hover gradient effect */}
                  <div className="absolute inset-0 bg-gradient-to-r from-pink-500/5 to-red-500/5 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none" />
                </div>
              </motion.div>
            ))}
          </motion.div>

          {/* Bottom Stats */}
          <motion.div
            variants={itemVariants}
            className="grid grid-cols-1 md:grid-cols-3 gap-8 pt-16"
          >
            <div className="text-center space-y-2">
              <div className="flex items-center justify-center">
                <Clock className="w-6 h-6 text-pink-500 mr-2" />
                <span className="text-2xl font-bold text-white">3 min</span>
              </div>
              <p className="text-muted-foreground">Average processing time</p>
            </div>

            <div className="text-center space-y-2">
              <div className="flex items-center justify-center">
                <BarChart3 className="w-6 h-6 text-pink-500 mr-2" />
                <span className="text-2xl font-bold text-white">94%</span>
              </div>
              <p className="text-muted-foreground">Viral prediction accuracy</p>
            </div>

            <div className="text-center space-y-2">
              <div className="flex items-center justify-center">
                <Users className="w-6 h-6 text-pink-500 mr-2" />
                <span className="text-2xl font-bold text-white">10K+</span>
              </div>
              <p className="text-muted-foreground">Happy creators</p>
            </div>
          </motion.div>
        </motion.div>
      </div>
    </section>
  )
}