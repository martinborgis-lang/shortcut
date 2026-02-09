'use client';

import { motion } from 'framer-motion';
import { Play, Hash, Instagram, MessageCircle } from 'lucide-react';

const platforms = [
  { icon: Play, name: 'YouTube', color: 'text-red-500' },
  { icon: Hash, name: 'TikTok', color: 'text-white' },
  { icon: Instagram, name: 'Instagram', color: 'text-pink-500' },
  { icon: MessageCircle, name: 'Twitch', color: 'text-purple-500' },
  { icon: Play, name: 'YouTube', color: 'text-red-500' },
  { icon: Hash, name: 'TikTok', color: 'text-white' },
  { icon: Instagram, name: 'Instagram', color: 'text-pink-500' },
  { icon: MessageCircle, name: 'Twitch', color: 'text-purple-500' },
  { icon: Play, name: 'YouTube', color: 'text-red-500' },
  { icon: Hash, name: 'TikTok', color: 'text-white' },
  { icon: Instagram, name: 'Instagram', color: 'text-pink-500' },
  { icon: MessageCircle, name: 'Twitch', color: 'text-purple-500' },
];

export default function SocialProof() {
  return (
    <section className="py-10 border-t border-b border-white/10 bg-white/[0.02]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Text */}
        <motion.p
          className="text-center text-lg text-gray-400 mb-8"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
        >
          Déjà adopté par{' '}
          <span className="bg-gradient-to-r from-purple-400 to-cyan-400 bg-clip-text text-transparent font-bold text-xl">
            2,000+
          </span>{' '}
          créateurs de contenu
        </motion.p>
      </div>

      {/* Marquee - full width with overflow hidden */}
      <div className="relative overflow-hidden">
        <motion.div
          className="flex gap-12"
          style={{ width: 'max-content' }}
          animate={{ x: ['0%', '-50%'] }}
          transition={{
            x: {
              repeat: Infinity,
              repeatType: 'loop',
              duration: 20,
              ease: 'linear',
            },
          }}
        >
          {[...platforms, ...platforms].map((platform, index) => {
            const Icon = platform.icon;
            return (
              <div
                key={index}
                className="flex items-center gap-3 whitespace-nowrap"
              >
                <Icon className={`h-7 w-7 ${platform.color}`} />
                <span className="text-gray-400 text-base font-medium">
                  {platform.name}
                </span>
              </div>
            );
          })}
        </motion.div>

        {/* Gradient Overlays */}
        <div className="absolute inset-y-0 left-0 w-24 bg-gradient-to-r from-zinc-950 to-transparent pointer-events-none" />
        <div className="absolute inset-y-0 right-0 w-24 bg-gradient-to-l from-zinc-950 to-transparent pointer-events-none" />
      </div>
    </section>
  );
}