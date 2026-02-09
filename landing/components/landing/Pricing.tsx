'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { Check, Star, MessageCircle } from 'lucide-react';

const plans = {
  monthly: {
    free: { price: '0', period: '/mois', originalPrice: null },
    pro: { price: '19', period: '/mois', originalPrice: null },
    business: { price: '49', period: '/mois', originalPrice: null },
  },
  annual: {
    free: { price: '0', period: '/mois', originalPrice: null },
    pro: { price: '15', period: '/mois', originalPrice: '19' },
    business: { price: '39', period: '/mois', originalPrice: '49' },
  },
};

const features = {
  free: [
    '60 min de vidéo/mois',
    '3 exports/mois',
    'Sous-titres auto',
    'Filigrane ShortCut',
  ],
  pro: [
    '300 min de vidéo/mois',
    'Exports illimités',
    'Sans filigrane',
    'Score de viralité',
    'Sous-titres personnalisables',
    'Recadrage IA',
    'Support prioritaire',
  ],
  business: [
    '1000 min de vidéo/mois',
    'Tout Pro inclus',
    'Multi-comptes (5 membres)',
    'API access',
    'Templates de marque',
    'Account manager dédié',
  ],
};

export default function Pricing() {
  const [isAnnual, setIsAnnual] = useState(false);
  const currentPlans = isAnnual ? plans.annual : plans.monthly;

  return (
    <section id="pricing" className="py-24">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <motion.div
          className="text-center mb-12 max-w-3xl mx-auto"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
        >
          <h2 className="text-3xl md:text-4xl lg:text-5xl font-bold mb-6">
            Des tarifs{' '}
            <span className="bg-gradient-to-r from-purple-400 to-cyan-400 bg-clip-text text-transparent">
              simples
            </span>
            , sans surprise
          </h2>
          <p className="text-lg text-gray-400 mb-10">
            Choisissez le plan qui correspond à vos besoins. Changez ou annulez
            à tout moment.
          </p>

          {/* Toggle - SEPARATE from cards, with proper spacing */}
          <div className="flex items-center justify-center gap-4">
            <span
              className={`text-base font-medium transition-colors ${
                !isAnnual ? 'text-white' : 'text-gray-500'
              }`}
            >
              Mensuel
            </span>

            <button
              className="relative w-14 h-7 rounded-full bg-gray-700 transition-colors duration-300 focus:outline-none focus:ring-2 focus:ring-purple-500/50"
              onClick={() => setIsAnnual(!isAnnual)}
              style={{
                backgroundColor: isAnnual ? '#8b5cf6' : '#374151',
              }}
            >
              <div
                className="absolute top-1 left-1 w-5 h-5 bg-white rounded-full transition-transform duration-300"
                style={{
                  transform: isAnnual ? 'translateX(28px)' : 'translateX(0)',
                }}
              />
            </button>

            <span
              className={`text-base font-medium transition-colors ${
                isAnnual ? 'text-white' : 'text-gray-500'
              }`}
            >
              Annuel
            </span>

            {isAnnual && (
              <motion.span
                className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-500/20 text-green-400 border border-green-500/30"
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
              >
                -20%
              </motion.span>
            )}
          </div>
        </motion.div>

        {/* Pricing Cards - mt-12 gives room below toggle */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-12 items-start">
          {/* Free Plan */}
          <motion.div
            className="bg-white/[0.03] border border-white/10 rounded-2xl p-8"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.1 }}
          >
            <div className="text-center mb-8">
              <h3 className="text-xl font-bold mb-2 text-white">Gratuit</h3>
              <div className="mb-1">
                <span className="text-4xl font-bold bg-gradient-to-r from-purple-400 to-cyan-400 bg-clip-text text-transparent">
                  {currentPlans.free.price}€
                </span>
                <span className="text-base text-gray-500">
                  {currentPlans.free.period}
                </span>
              </div>
              <p className="text-gray-500 text-sm">Pour découvrir ShortCut</p>
            </div>

            <ul className="space-y-3 mb-8">
              {features.free.map((feature, index) => (
                <li key={index} className="flex items-start gap-3">
                  <Check className="h-5 w-5 text-green-500 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-300 text-sm">{feature}</span>
                </li>
              ))}
            </ul>

            <motion.button
              className="w-full py-3 px-6 rounded-xl border border-white/20 text-gray-300 text-sm font-medium hover:bg-white/5 transition-all duration-200"
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              Commencer gratuitement
            </motion.button>
          </motion.div>

          {/* Pro Plan - Featured */}
          <motion.div
            className="relative bg-white/[0.05] border-2 border-purple-500 rounded-2xl p-8 shadow-lg shadow-purple-500/10"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.2 }}
          >
            {/* Popular Badge - on the CARD, not the toggle */}
            <div className="absolute -top-3.5 left-1/2 -translate-x-1/2 z-10">
              <div className="flex items-center gap-1.5 bg-gradient-to-r from-purple-600 to-cyan-500 px-4 py-1 rounded-full text-white text-xs font-semibold whitespace-nowrap shadow-md">
                <Star className="h-3.5 w-3.5" />
                <span>Populaire</span>
              </div>
            </div>

            <div className="text-center mb-8 mt-2">
              <h3 className="text-xl font-bold mb-2 text-white">Pro</h3>
              <div className="mb-1">
                <span className="text-4xl font-bold bg-gradient-to-r from-purple-400 to-cyan-400 bg-clip-text text-transparent">
                  {currentPlans.pro.price}€
                </span>
                <span className="text-base text-gray-500">
                  {currentPlans.pro.period}
                </span>
              </div>
              {isAnnual && currentPlans.pro.originalPrice && (
                <div className="text-sm text-gray-600 line-through">
                  {currentPlans.pro.originalPrice}€/mois
                </div>
              )}
              <p className="text-gray-500 text-sm mt-1">
                Pour les créateurs actifs
              </p>
            </div>

            <ul className="space-y-3 mb-8">
              {features.pro.map((feature, index) => (
                <li key={index} className="flex items-start gap-3">
                  <Check className="h-5 w-5 text-green-500 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-300 text-sm">{feature}</span>
                </li>
              ))}
            </ul>

            <motion.button
              className="w-full py-3 px-6 rounded-xl bg-gradient-to-r from-purple-600 to-cyan-500 text-white text-sm font-semibold hover:shadow-xl hover:shadow-purple-500/20 transition-all duration-200"
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              Essai gratuit 7 jours
            </motion.button>
          </motion.div>

          {/* Business Plan */}
          <motion.div
            className="bg-white/[0.03] border border-white/10 rounded-2xl p-8"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.3 }}
          >
            <div className="text-center mb-8">
              <h3 className="text-xl font-bold mb-2 text-white">Business</h3>
              <div className="mb-1">
                <span className="text-4xl font-bold bg-gradient-to-r from-purple-400 to-cyan-400 bg-clip-text text-transparent">
                  {currentPlans.business.price}€
                </span>
                <span className="text-base text-gray-500">
                  {currentPlans.business.period}
                </span>
              </div>
              {isAnnual && currentPlans.business.originalPrice && (
                <div className="text-sm text-gray-600 line-through">
                  {currentPlans.business.originalPrice}€/mois
                </div>
              )}
              <p className="text-gray-500 text-sm mt-1">Pour les équipes</p>
            </div>

            <ul className="space-y-3 mb-8">
              {features.business.map((feature, index) => (
                <li key={index} className="flex items-start gap-3">
                  <Check className="h-5 w-5 text-green-500 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-300 text-sm">{feature}</span>
                </li>
              ))}
            </ul>

            <motion.button
              className="w-full py-3 px-6 rounded-xl border border-purple-500/50 text-purple-400 text-sm font-medium hover:bg-purple-500/10 transition-all duration-200 flex items-center justify-center gap-2"
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              <MessageCircle className="h-4 w-4" />
              <span>Nous contacter</span>
            </motion.button>
          </motion.div>
        </div>

        {/* Bottom Note */}
        <motion.p
          className="text-center mt-10 text-gray-500 text-sm"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, delay: 0.4 }}
        >
          Tous les plans incluent des mises à jour gratuites.
          <br />
          Aucun engagement, annulation possible à tout moment.
        </motion.p>
      </div>
    </section>
  );
}