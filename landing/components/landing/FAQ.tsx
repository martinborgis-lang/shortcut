'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown, ArrowRight } from 'lucide-react';

const faqs = [
  {
    id: 1,
    question: 'Quels types de vidéos sont supportés ?',
    answer:
      'ShortCut supporte les vidéos YouTube et Twitch. Le support Vimeo et les fichiers locaux arrivent bientôt. Nous acceptons toutes les résolutions et durées.',
  },
  {
    id: 2,
    question: 'Combien de temps prend la génération des clips ?',
    answer:
      "En moyenne 2-5 minutes pour une vidéo d'1 heure. Le temps varie selon la durée de votre vidéo et la complexité du contenu. Vous recevez une notification quand vos clips sont prêts.",
  },
  {
    id: 3,
    question: 'Les sous-titres sont-ils précis ?',
    answer:
      "Oui, notre IA atteint 97%+ de précision pour le français et l'anglais. Vous pouvez éditer manuellement si besoin. Nous supportons plus de 20 langues avec une précision élevée.",
  },
  {
    id: 4,
    question: 'Puis-je personnaliser le style des shorts ?',
    answer:
      'Absolument. Choisissez parmi nos templates, personnalisez les couleurs des sous-titres, ajoutez votre logo et votre intro/outro. Le plan Pro débloque la personnalisation complète.',
  },
  {
    id: 5,
    question: "Y a-t-il un engagement ?",
    answer:
      'Aucun engagement. Vous pouvez annuler à tout moment sans frais. Le plan gratuit reste disponible indéfiniment avec 60 minutes par mois.',
  },
  {
    id: 6,
    question: 'Comment fonctionne le score de viralité ?',
    answer:
      'Notre IA analyse le rythme, les émotions, les hooks et les tendances actuelles pour attribuer un score de 0 à 100 à chaque clip. Plus le score est élevé, plus le potentiel viral est important.',
  },
  {
    id: 7,
    question: 'Puis-je publier directement sur TikTok ?',
    answer:
      'Oui, connectez vos comptes TikTok, YouTube et Instagram pour publier en un clic depuis ShortCut. La fonction de publication automatique est disponible sur tous les plans payants.',
  },
];

export default function FAQ() {
  const [openId, setOpenId] = useState<number | null>(1);

  return (
    <section id="faq" className="py-24 bg-white/[0.02]">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <motion.div
          className="text-center mb-14"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
        >
          <h2 className="text-3xl md:text-4xl lg:text-5xl font-bold mb-6">
            Questions{' '}
            <span className="bg-gradient-to-r from-purple-400 to-cyan-400 bg-clip-text text-transparent">
              fréquentes
            </span>
          </h2>
          <p className="text-lg text-gray-400">
            Tout ce que vous devez savoir sur ShortCut
          </p>
        </motion.div>

        {/* FAQ Items */}
        <div className="space-y-3">
          {faqs.map((faq, index) => (
            <motion.div
              key={faq.id}
              className="bg-white/[0.03] border border-white/10 rounded-xl overflow-hidden"
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6, delay: index * 0.05 }}
            >
              <button
                className="w-full px-6 py-5 text-left flex items-center justify-between gap-4 hover:bg-white/[0.03] transition-colors duration-200"
                onClick={() => setOpenId(openId === faq.id ? null : faq.id)}
              >
                <h3 className="text-base font-semibold text-white">
                  {faq.question}
                </h3>
                <motion.div
                  animate={{ rotate: openId === faq.id ? 180 : 0 }}
                  transition={{ duration: 0.2 }}
                  className="flex-shrink-0"
                >
                  <ChevronDown className="h-5 w-5 text-gray-400" />
                </motion.div>
              </button>

              <AnimatePresence>
                {openId === faq.id && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.3 }}
                    className="overflow-hidden"
                  >
                    <div className="px-6 pb-5">
                      <p className="text-gray-400 leading-relaxed text-sm">
                        {faq.answer}
                      </p>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          ))}
        </div>

        {/* Contact CTA */}
        <motion.div
          className="text-center mt-12"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, delay: 0.3 }}
        >
          <p className="text-gray-500 mb-3 text-sm">
            Vous avez d&apos;autres questions ?
          </p>
          <button className="inline-flex items-center gap-2 text-purple-400 hover:text-purple-300 transition-colors duration-200 text-sm font-medium">
            <span>Contactez notre support</span>
            <ArrowRight className="h-4 w-4" />
          </button>
        </motion.div>
      </div>
    </section>
  );
}