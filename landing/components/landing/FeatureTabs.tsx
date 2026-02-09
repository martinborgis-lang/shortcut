'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Scissors, Type, Crop, TrendingUp, Play } from 'lucide-react';

const features = [
  {
    id: 'ai-cutting',
    title: 'Découpage IA',
    description:
      'Notre IA analyse votre vidéo et extrait les 10 meilleurs moments à fort potentiel viral. Chaque clip est scoré de 0 à 100.',
    icon: Scissors,
    mockupGradient: 'from-purple-500 to-pink-500',
  },
  {
    id: 'dynamic-subtitles',
    title: 'Sous-titres dynamiques',
    description:
      'Des sous-titres animés mot par mot, style TikTok, avec détection automatique de la langue. Personnalisez les couleurs et la police.',
    icon: Type,
    mockupGradient: 'from-blue-500 to-cyan-500',
  },
  {
    id: 'smart-reframe',
    title: 'Recadrage intelligent',
    description:
      'Passage automatique du 16:9 au 9:16 avec tracking du visage du speaker. Le sujet reste toujours centré.',
    icon: Crop,
    mockupGradient: 'from-green-500 to-emerald-500',
  },
  {
    id: 'viral-score',
    title: 'Score de viralité',
    description:
      "Chaque clip reçoit un score basé sur l'analyse de millions de shorts viraux. Publiez uniquement les meilleurs.",
    icon: TrendingUp,
    mockupGradient: 'from-orange-500 to-red-500',
  },
];

export default function FeatureTabs() {
  const [activeTab, setActiveTab] = useState('ai-cutting');
  const activeFeature = features.find((f) => f.id === activeTab)!;

  return (
    <section id="features" className="py-24">
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
            L&apos;IA qui comprend{' '}
            <span className="bg-gradient-to-r from-purple-400 to-cyan-400 bg-clip-text text-transparent">
              chaque seconde
            </span>{' '}
            de votre vidéo
          </h2>
          <p className="text-lg text-gray-400">
            Des modèles IA entraînés pour détecter les moments viraux, recadrer
            et sous-titrer automatiquement.
          </p>
        </motion.div>

        {/* Two Column Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 lg:gap-16 items-start">
          {/* LEFT: Tabs Navigation */}
          <motion.div
            className="order-2 lg:order-1 flex flex-col gap-4"
            initial={{ opacity: 0, x: -20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
          >
            {features.map((feature) => {
              const Icon = feature.icon;
              const isActive = activeTab === feature.id;

              return (
                <button
                  key={feature.id}
                  onClick={() => setActiveTab(feature.id)}
                  className={`w-full text-left p-5 rounded-2xl border transition-all duration-300 ${
                    isActive
                      ? 'bg-white/10 border-purple-500/50 shadow-lg shadow-purple-500/5'
                      : 'bg-white/[0.03] border-white/10 hover:bg-white/[0.06]'
                  }`}
                >
                  <div className="flex items-start gap-4">
                    <div
                      className={`flex-shrink-0 w-11 h-11 rounded-xl flex items-center justify-center ${
                        isActive
                          ? 'bg-gradient-to-r from-purple-600 to-cyan-500'
                          : 'bg-white/10'
                      }`}
                    >
                      <Icon className="h-5 w-5 text-white" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <h3
                        className={`text-base font-semibold mb-1 ${
                          isActive ? 'text-white' : 'text-gray-300'
                        }`}
                      >
                        {feature.title}
                      </h3>
                      <p
                        className={`text-sm leading-relaxed ${
                          isActive ? 'text-gray-300' : 'text-gray-500'
                        }`}
                      >
                        {feature.description}
                      </p>
                    </div>
                  </div>
                </button>
              );
            })}
          </motion.div>

          {/* RIGHT: Content Display / Mockup */}
          <motion.div
            className="order-1 lg:order-2"
            initial={{ opacity: 0, x: 20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
          >
            <div className="relative w-full aspect-[4/3] lg:aspect-auto lg:h-[520px] rounded-2xl overflow-hidden">
              <AnimatePresence mode="wait">
                <motion.div
                  key={activeFeature.id}
                  className={`absolute inset-0 bg-gradient-to-br ${activeFeature.mockupGradient} flex items-center justify-center`}
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.95 }}
                  transition={{ duration: 0.3 }}
                >
                  <div className="text-center text-white p-8">
                    <div className="w-20 h-20 mx-auto mb-6 rounded-2xl bg-white/20 backdrop-blur-sm flex items-center justify-center">
                      <activeFeature.icon className="h-10 w-10" />
                    </div>
                    <h3 className="text-2xl font-bold mb-2">
                      {activeFeature.title}
                    </h3>
                    <p className="text-white/70 max-w-sm mx-auto mb-8">
                      Aperçu de la fonctionnalité – Mockup à remplacer
                    </p>
                    <motion.div
                      className="inline-flex items-center gap-2 bg-white/20 backdrop-blur-sm px-5 py-2.5 rounded-full cursor-pointer"
                      whileHover={{ scale: 1.05, backgroundColor: 'rgba(255,255,255,0.3)' }}
                    >
                      <Play className="h-4 w-4" />
                      <span className="text-sm font-medium">Voir la démo</span>
                    </motion.div>
                  </div>
                </motion.div>
              </AnimatePresence>
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}