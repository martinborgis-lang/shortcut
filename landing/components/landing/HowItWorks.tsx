'use client';

import { motion } from 'framer-motion';
import { Link, Sparkles, Download } from 'lucide-react';

const steps = [
  {
    number: '01',
    title: 'Collez votre lien',
    description:
      "Copiez l'URL de votre vidéo YouTube ou Twitch et collez-la dans ShortCut.",
    icon: Link,
    gradient: 'from-purple-500 to-pink-500',
  },
  {
    number: '02',
    title: "L'IA fait le travail",
    description:
      'En quelques minutes, notre IA découpe, recadre et sous-titre vos meilleurs moments.',
    icon: Sparkles,
    gradient: 'from-blue-500 to-cyan-500',
  },
  {
    number: '03',
    title: 'Téléchargez & publiez',
    description:
      'Téléchargez vos shorts ou publiez directement sur TikTok, Reels et YouTube Shorts.',
    icon: Download,
    gradient: 'from-green-500 to-emerald-500',
  },
];

export default function HowItWorks() {
  return (
    <section className="py-24 bg-white/[0.02]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <motion.div
          className="text-center mb-16 max-w-3xl mx-auto"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
        >
          <h2 className="text-3xl md:text-4xl lg:text-5xl font-bold mb-6">
            Créez vos shorts en{' '}
            <span className="bg-gradient-to-r from-purple-400 to-cyan-400 bg-clip-text text-transparent">
              3 étapes
            </span>
          </h2>
          <p className="text-lg text-gray-400">
            Un processus simple et automatisé pour transformer vos vidéos
            longues en clips viraux.
          </p>
        </motion.div>

        {/* Steps Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 lg:gap-10">
          {steps.map((step, index) => {
            const Icon = step.icon;

            return (
              <motion.div
                key={step.number}
                className="relative pt-6"
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.6, delay: index * 0.2 }}
              >
                {/* Card - position relative so the badge positions against it */}
                <div className="relative bg-white/[0.05] backdrop-blur-sm border border-white/10 rounded-2xl p-8 text-center h-full hover:bg-white/[0.08] transition-all duration-300">
                  {/* Step Number Badge - positioned relative to this card */}
                  <div className="absolute -top-4 left-1/2 -translate-x-1/2 z-10">
                    <div
                      className={`w-10 h-10 rounded-full bg-gradient-to-r ${step.gradient} flex items-center justify-center text-white font-bold text-sm shadow-lg`}
                    >
                      {step.number}
                    </div>
                  </div>

                  {/* Icon - INSIDE the card, in normal flow */}
                  <div className="flex justify-center mb-5 mt-2">
                    <div
                      className={`w-14 h-14 rounded-2xl bg-gradient-to-r ${step.gradient} flex items-center justify-center shadow-lg`}
                    >
                      <Icon className="h-7 w-7 text-white" />
                    </div>
                  </div>

                  {/* Content */}
                  <h3 className="text-xl font-bold text-white mb-3">
                    {step.title}
                  </h3>
                  <p className="text-gray-400 leading-relaxed text-sm">
                    {step.description}
                  </p>
                </div>

                {/* Arrow for Mobile between cards */}
                {index < steps.length - 1 && (
                  <div className="md:hidden flex justify-center mt-6">
                    <motion.div
                      className="w-0.5 h-8 bg-gradient-to-b from-purple-500 to-cyan-500 rounded-full"
                      animate={{ opacity: [0.3, 1, 0.3] }}
                      transition={{ duration: 2, repeat: Infinity }}
                    />
                  </div>
                )}
              </motion.div>
            );
          })}
        </div>

        {/* Desktop Connection Line (decorative) */}
        <div className="hidden md:flex justify-center -mt-[calc(50%+2rem)] mb-[calc(50%-2rem)] pointer-events-none" aria-hidden>
          {/* We skip the decorative line to avoid layout issues */}
        </div>

        {/* Bottom CTA */}
        <motion.div
          className="relative z-10 text-center mt-16"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, delay: 0.6 }}
        >
          <p className="text-gray-400 mb-6">
            Prêt à commencer ? Aucune inscription requise pour essayer.
          </p>
          <motion.button
            className="px-8 py-4 bg-gradient-to-r from-purple-600 to-cyan-500 rounded-2xl text-white font-semibold text-lg hover:shadow-xl hover:shadow-purple-500/20 transition-all duration-300"
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            Essayer gratuitement
          </motion.button>
        </motion.div>
      </div>
    </section>
  );
}