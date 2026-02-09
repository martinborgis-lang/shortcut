"use client"

import { motion } from "framer-motion"
import { Link, Sparkles, Share, ArrowRight } from "lucide-react"

const steps = [
  {
    number: "01",
    title: "Paste YouTube Link",
    description: "Drop any YouTube URL and our AI analyzes the content to identify the most engaging moments",
    icon: <Link className="w-8 h-8" />,
    color: "from-blue-500 to-purple-500"
  },
  {
    number: "02",
    title: "AI Generates Shorts",
    description: "Get viral moments with perfect timing, auto-cropping, and professional subtitle styles",
    icon: <Sparkles className="w-8 h-8" />,
    color: "from-purple-500 to-pink-500"
  },
  {
    number: "03",
    title: "Publish on TikTok",
    description: "Schedule and auto-post to TikTok, Instagram, and YouTube at optimal engagement times",
    icon: <Share className="w-8 h-8" />,
    color: "from-pink-500 to-red-500"
  }
]

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.2
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

export function HowItWorks() {
  return (
    <section className="py-24 bg-background" id="how-it-works">
      <div className="section-container">
        <motion.div
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-100px" }}
          variants={containerVariants}
          className="text-center space-y-16"
        >
          {/* Header */}
          <motion.div variants={itemVariants} className="space-y-4">
            <h2 className="text-3xl md:text-4xl lg:text-5xl font-bold text-white">
              How it Works
            </h2>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              From YouTube to viral TikTok in just 3 simple steps. Our AI does the heavy lifting.
            </p>
          </motion.div>

          {/* Steps */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 lg:gap-12">
            {steps.map((step, index) => (
              <motion.div
                key={step.number}
                variants={itemVariants}
                className="relative"
              >
                {/* Connector Line */}
                {index < steps.length - 1 && (
                  <div className="hidden md:block absolute top-24 left-full w-full h-0.5 bg-gradient-to-r from-muted to-transparent z-0" />
                )}

                {/* Step Card */}
                <div className="relative bg-card/50 backdrop-blur-sm rounded-2xl p-8 border border-border hover:bg-card/80 transition-all duration-300 group">
                  {/* Step Number */}
                  <div className="absolute -top-4 -left-4">
                    <div className={`w-12 h-12 bg-gradient-to-r ${step.color} rounded-full flex items-center justify-center text-white font-bold text-lg shadow-lg`}>
                      {step.number}
                    </div>
                  </div>

                  {/* Icon */}
                  <div className={`w-16 h-16 bg-gradient-to-r ${step.color} rounded-xl flex items-center justify-center text-white mb-6 group-hover:scale-110 transition-transform duration-300`}>
                    {step.icon}
                  </div>

                  {/* Content */}
                  <div className="space-y-4">
                    <h3 className="text-xl font-semibold text-white">
                      {step.title}
                    </h3>
                    <p className="text-muted-foreground leading-relaxed">
                      {step.description}
                    </p>
                  </div>

                  {/* Arrow */}
                  {index < steps.length - 1 && (
                    <div className="md:hidden flex justify-center mt-8">
                      <ArrowRight className="w-6 h-6 text-muted-foreground" />
                    </div>
                  )}
                </div>
              </motion.div>
            ))}
          </div>

          {/* Bottom CTA */}
          <motion.div variants={itemVariants} className="pt-8">
            <p className="text-muted-foreground mb-6">
              Ready to create viral content?
            </p>
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="inline-flex items-center px-8 py-4 bg-gradient-to-r from-pink-500 to-red-500 hover:from-pink-600 hover:to-red-600 text-white font-semibold rounded-lg transition-all duration-300 shadow-lg hover:shadow-xl"
            >
              Get Started Now <ArrowRight className="ml-2 h-5 w-5" />
            </motion.button>
          </motion.div>
        </motion.div>
      </div>
    </section>
  )
}