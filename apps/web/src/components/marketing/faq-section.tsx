"use client"

import { motion } from "framer-motion"
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion"

const faqs = [
  {
    question: "How accurate is the AI at finding viral moments?",
    answer: "Our AI analyzes millions of viral TikToks to identify patterns and has a 94% accuracy rate at predicting viral content. It's trained on engagement data from top creators and understands what makes content go viral - from hook strength and emotional peaks to visual storytelling and timing."
  },
  {
    question: "What video platforms does ShortCut support?",
    answer: "Currently we support YouTube videos, Twitch VODs, and direct video uploads (MP4, MOV, AVI). We can process videos up to 4 hours long and export to all major social platforms including TikTok, Instagram Reels, YouTube Shorts, and Twitter. More platforms are being added based on user feedback."
  },
  {
    question: "Can I edit the clips before posting?",
    answer: "Absolutely! You have full control over every aspect of your clips. Edit timing, change subtitle styles, customize titles and descriptions, adjust cropping, add your brand colors, and modify any element before publishing. Our editor is designed to be powerful yet intuitive for creators of all skill levels."
  },
  {
    question: "Do you support automatic posting to TikTok?",
    answer: "Yes! Connect your TikTok, Instagram, and YouTube accounts for seamless auto-posting. Schedule your clips to go live at optimal times, add custom captions and hashtags, and track performance all from one dashboard. We also support bulk scheduling for efficient content planning."
  },
  {
    question: "What's included in the free plan?",
    answer: "The free plan includes 30 minutes of video processing per month, 5 clips, basic subtitle styles, 720p export quality, and community support. It's perfect for trying out ShortCut and getting familiar with AI-powered clipping before upgrading to unlock unlimited clips and advanced features."
  },
  {
    question: "How long does it take to process a video?",
    answer: "Most videos under 1 hour process in 3-5 minutes. Longer videos may take up to 15 minutes. Processing time depends on video length, quality, and current server load. Pro users get priority processing for faster turnaround times. You'll receive an email notification when your clips are ready."
  },
  {
    question: "What makes ShortCut different from other video editors?",
    answer: "Unlike traditional editors, ShortCut is built specifically for viral content creation. Our AI understands social media trends, optimal clip timing, and engagement patterns. We automate the time-consuming parts (finding moments, cropping, subtitles) so you can focus on creativity and growing your audience."
  },
  {
    question: "Can I cancel my subscription anytime?",
    answer: "Yes, you can cancel your subscription at any time with no cancellation fees. Your subscription will remain active until the end of your current billing period, and you'll retain access to all downloaded clips. We also offer a 7-day free trial so you can test all features risk-free before committing."
  }
]

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.05
    }
  }
}

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.6,
      ease: "easeOut"
    }
  }
}

export function FAQSection() {
  return (
    <section className="py-24 bg-background" id="faq">
      <div className="section-container">
        <motion.div
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-100px" }}
          variants={containerVariants}
          className="max-w-4xl mx-auto space-y-12"
        >
          {/* Header */}
          <motion.div variants={itemVariants} className="text-center space-y-4">
            <h2 className="text-3xl md:text-4xl lg:text-5xl font-bold text-white">
              Frequently Asked Questions
            </h2>
            <p className="text-lg text-muted-foreground">
              Everything you need to know about ShortCut and creating viral content.
            </p>
          </motion.div>

          {/* FAQ Accordion */}
          <motion.div variants={containerVariants}>
            <Accordion type="single" collapsible className="space-y-4">
              {faqs.map((faq, index) => (
                <motion.div key={index} variants={itemVariants}>
                  <AccordionItem
                    value={`item-${index}`}
                    className="bg-card/50 backdrop-blur-sm border border-border rounded-xl px-6 hover:bg-card/80 transition-colors duration-300"
                  >
                    <AccordionTrigger className="text-white hover:text-white/80 py-6 text-left font-medium">
                      {faq.question}
                    </AccordionTrigger>
                    <AccordionContent className="text-muted-foreground leading-relaxed pb-6">
                      {faq.answer}
                    </AccordionContent>
                  </AccordionItem>
                </motion.div>
              ))}
            </Accordion>
          </motion.div>

          {/* Bottom CTA */}
          <motion.div variants={itemVariants} className="text-center space-y-6 pt-8">
            <div className="space-y-2">
              <h3 className="text-xl font-semibold text-white">
                Still have questions?
              </h3>
              <p className="text-muted-foreground">
                Our team is here to help you succeed with your content creation.
              </p>
            </div>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <motion.a
                href="mailto:support@shortcut.app"
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="inline-flex items-center justify-center px-6 py-3 bg-card border border-border text-white rounded-lg hover:bg-card/80 transition-colors duration-300"
              >
                Email Support
              </motion.a>
              <motion.a
                href="/contact"
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="inline-flex items-center justify-center px-6 py-3 bg-gradient-to-r from-pink-500 to-red-500 hover:from-pink-600 hover:to-red-600 text-white rounded-lg transition-all duration-300"
              >
                Schedule a Call
              </motion.a>
            </div>
          </motion.div>
        </motion.div>
      </div>
    </section>
  )
}