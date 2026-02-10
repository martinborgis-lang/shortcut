'use client';

import { motion } from 'framer-motion';
import { Star, Quote } from 'lucide-react';

const testimonials = [
  {
    id: 1,
    name: 'Alex Martin',
    handle: '@alexgaming',
    avatar: 'AM',
    quote:
      "J'ai gagné 3h par semaine depuis que j'utilise ShortCut. Mes shorts TikTok ont explosé.",
    stat: '3h/semaine gagnées',
    color: 'from-purple-500 to-pink-500',
  },
  {
    id: 2,
    name: 'Sarah Chen',
    handle: '@sarahtech',
    avatar: 'SC',
    quote:
      'Le score de viralité est bluffant. 8 clips sur 10 dépassent les 10K vues.',
    stat: '80% de succès',
    color: 'from-blue-500 to-cyan-500',
  },
  {
    id: 3,
    name: 'Thomas Durand',
    handle: '@thomasstream',
    avatar: 'TD',
    quote:
      'Je ne fais plus de montage. Je colle mon lien et ShortCut fait tout.',
    stat: '100% automatisé',
    color: 'from-green-500 to-emerald-500',
  },
  {
    id: 4,
    name: 'Marie Dubois',
    handle: '@mariecreative',
    avatar: 'MD',
    quote:
      'Mes vues YouTube Shorts ont augmenté de 200% en 2 mois.',
    stat: '+200% de vues',
    color: 'from-orange-500 to-red-500',
  },
  {
    id: 5,
    name: 'Kevin Roux',
    handle: '@kevinpro',
    avatar: 'KR',
    quote:
      "L'outil parfait pour les streamers Twitch qui veulent percer sur TikTok.",
    stat: 'Twitch vers TikTok',
    color: 'from-indigo-500 to-purple-500',
  },
  {
    id: 6,
    name: 'Lisa Wang',
    handle: '@lisaedits',
    avatar: 'LW',
    quote:
      'Les sous-titres dynamiques donnent un rendu ultra pro sans effort.',
    stat: 'Qualité pro',
    color: 'from-pink-500 to-rose-500',
  },
];

export default function Testimonials() {
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
            Ce que disent nos{' '}
            <span className="bg-gradient-to-r from-purple-400 to-cyan-400 bg-clip-text text-transparent">
              utilisateurs
            </span>
          </h2>
          <p className="text-lg text-gray-400">
            Des créateurs de contenu qui ont transformé leur workflow grâce à
            ShortCut.
          </p>
        </motion.div>

        {/* Testimonials Grid - static, no overflow */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {testimonials.map((testimonial, index) => (
            <motion.div
              key={testimonial.id}
              className="bg-white/[0.05] border border-white/10 rounded-2xl p-6 hover:bg-white/[0.08] transition-all duration-300 flex flex-col"
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6, delay: index * 0.1 }}
            >
              {/* Quote Icon */}
              <Quote className="h-8 w-8 text-purple-400 mb-4 flex-shrink-0" />

              {/* Quote Text */}
              <blockquote className="text-gray-300 mb-5 leading-relaxed flex-1">
                &ldquo;{testimonial.quote}&rdquo;
              </blockquote>

              {/* Stats Badge */}
              <div className="mb-4">
                <span
                  className={`inline-block px-3 py-1 rounded-full text-xs font-medium text-white bg-gradient-to-r ${testimonial.color}`}
                >
                  {testimonial.stat}
                </span>
              </div>

              {/* Author */}
              <div className="flex items-center gap-3">
                <div
                  className={`w-10 h-10 rounded-full bg-gradient-to-r ${testimonial.color} flex items-center justify-center text-white font-bold text-xs flex-shrink-0`}
                >
                  {testimonial.avatar}
                </div>
                <div className="min-w-0">
                  <div className="font-semibold text-white text-sm truncate">
                    {testimonial.name}
                  </div>
                  <div className="text-gray-500 text-xs truncate">
                    {testimonial.handle}
                  </div>
                </div>
              </div>

              {/* Rating Stars */}
              <div className="flex items-center mt-4 gap-0.5">
                {[...Array(5)].map((_, i) => (
                  <Star
                    key={i}
                    className="h-4 w-4 text-yellow-400 fill-yellow-400"
                  />
                ))}
              </div>
            </motion.div>
          ))}
        </div>

        {/* Bottom CTA */}
        <motion.div
          className="text-center mt-16"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, delay: 0.3 }}
        >
          <p className="text-gray-400 mb-6">
            Rejoignez des milliers de créateurs satisfaits
          </p>
          <motion.button
            className="px-8 py-4 bg-gradient-to-r from-purple-600 to-cyan-500 rounded-2xl text-white font-semibold text-lg hover:shadow-xl hover:shadow-purple-500/20 transition-all duration-300"
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            Commencer gratuitement
          </motion.button>
        </motion.div>
      </div>
    </section>
  );
}