'use client';

import { motion } from 'framer-motion';
import { ArrowRight, Sparkles } from 'lucide-react';
import Link from 'next/link';

export default function FinalCTA() {
  return (
    <section className="py-24 relative overflow-hidden">
      {/* Background */}
      <div className="absolute inset-0 bg-gradient-to-r from-purple-700 via-purple-600 to-cyan-600" />
      <div className="absolute inset-0 bg-black/20" />

      <div className="relative max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        {/* Decorative circles */}
        <div className="absolute top-10 left-10 w-20 h-20 border border-white/10 rounded-full hidden sm:block" />
        <div className="absolute bottom-10 right-10 w-14 h-14 border border-white/10 rounded-full hidden sm:block" />

        {/* Icon */}
        <motion.div
          className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-white/10 backdrop-blur-sm mb-8"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
        >
          <Sparkles className="h-8 w-8 text-white" />
        </motion.div>

        {/* Headline */}
        <motion.h2
          className="text-3xl md:text-5xl lg:text-6xl font-extrabold text-white mb-6 leading-tight"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, delay: 0.1 }}
        >
          Prêt à transformer vos vidéos
          <br />
          en <span className="text-yellow-300">machine à vues</span> ?
        </motion.h2>

        {/* Subtitle */}
        <motion.p
          className="text-lg md:text-xl text-white/80 mb-10 max-w-2xl mx-auto leading-relaxed"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, delay: 0.2 }}
        >
          Rejoignez{' '}
          <span className="font-bold text-yellow-300">2,000+</span> créateurs.
          Commencez gratuitement,{' '}
          <span className="font-semibold">sans carte bancaire.</span>
        </motion.p>

        {/* CTA Button */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, delay: 0.3 }}
        >
          <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
            <Link
              href="/sign-up"
              className="inline-flex items-center gap-3 px-10 py-5 bg-white text-purple-700 rounded-full text-lg font-bold hover:bg-gray-100 transition-all duration-300 shadow-2xl"
            >
              <span>Commencer gratuitement</span>
              <ArrowRight className="h-5 w-5" />
            </Link>
          </motion.div>
        </motion.div>

        {/* Trust Indicators */}
        <motion.div
          className="flex flex-col sm:flex-row items-center justify-center gap-4 sm:gap-6 mt-8 text-white/70"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, delay: 0.4 }}
        >
          <div className="flex items-center gap-2">
            <div className="w-1.5 h-1.5 bg-green-400 rounded-full" />
            <span className="text-sm">Essai gratuit 7 jours</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-1.5 h-1.5 bg-green-400 rounded-full" />
            <span className="text-sm">Aucune carte bancaire</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-1.5 h-1.5 bg-green-400 rounded-full" />
            <span className="text-sm">Annulation à tout moment</span>
          </div>
        </motion.div>
      </div>
    </section>
  );
}