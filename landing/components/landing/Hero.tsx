'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { Rocket, ArrowRight, Play } from 'lucide-react';

export default function Hero() {
  const [url, setUrl] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    console.log('URL:', url);
  };

  return (
    <section
      id="hero"
      className="relative min-h-screen flex items-center justify-center overflow-hidden pt-16"
    >
      {/* Background */}
      <div className="absolute inset-0 bg-zinc-950">
        <div
          className="absolute inset-0 opacity-20"
          style={{
            backgroundImage: 'linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px)',
            backgroundSize: '60px 60px',
          }}
        />
        <div className="absolute inset-0 bg-gradient-to-br from-purple-600/20 via-transparent to-cyan-500/20" />
      </div>

      <div className="relative w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center py-20">
        {/* Badge */}
        <motion.div
          className="inline-flex items-center gap-2 bg-white/5 backdrop-blur-sm border border-white/10 rounded-full px-4 py-2 mb-8"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <Rocket className="h-4 w-4 text-purple-400" />
          <span className="text-sm text-gray-300">L&apos;outil #1 de clipping IA pour créateurs</span>
        </motion.div>

        {/* Main Headline */}
        <motion.h1
          className="text-4xl md:text-6xl lg:text-7xl font-extrabold mb-8 leading-tight"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.1 }}
        >
          <span className="text-white">1 vidéo longue,</span>
          <br />
          <span className="bg-gradient-to-r from-purple-400 to-cyan-400 bg-clip-text text-transparent">
            10 shorts viraux.
          </span>
          <br />
          <span className="text-white">Créez </span>
          <span className="bg-gradient-to-r from-purple-400 to-cyan-400 bg-clip-text text-transparent">
            10x plus vite.
          </span>
        </motion.h1>

        {/* Subtitle */}
        <motion.p
          className="text-lg md:text-xl lg:text-2xl text-gray-400 mb-12 max-w-3xl mx-auto leading-relaxed"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
        >
          ShortCut transforme vos vidéos YouTube et Twitch en clips prêts à poster sur{' '}
          <span className="bg-gradient-to-r from-purple-400 to-cyan-400 bg-clip-text text-transparent font-medium">
            TikTok, Reels et Shorts
          </span>{' '}
          — en un clic.
        </motion.p>

        {/* URL Input Form */}
        <motion.form
          onSubmit={handleSubmit}
          className="w-full max-w-2xl mx-auto mb-8"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.3 }}
        >
          <div className="relative flex flex-col sm:flex-row gap-3 sm:gap-0 p-2 bg-white/5 backdrop-blur-sm border border-white/20 rounded-2xl shadow-lg shadow-purple-500/5">
            <input
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="Collez votre lien YouTube ou Twitch..."
              className="flex-1 px-5 py-3 bg-transparent text-white placeholder-gray-500 focus:outline-none text-base"
            />
            <motion.button
              type="submit"
              className="px-6 py-3 bg-gradient-to-r from-purple-600 to-cyan-500 rounded-xl text-white font-semibold flex items-center justify-center gap-2 hover:shadow-xl hover:shadow-purple-500/20 transition-all duration-300 whitespace-nowrap"
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              <span>Générer mes clips</span>
              <ArrowRight className="h-5 w-5" />
            </motion.button>
          </div>
        </motion.form>

        {/* Platform Logos */}
        <motion.div
          className="flex flex-wrap items-center justify-center gap-3 sm:gap-6"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.4 }}
        >
          <span className="text-sm text-gray-500">Plateformes supportées :</span>
          <div className="flex items-center gap-4">
            {/* YouTube */}
            <div className="w-8 h-8 bg-red-600 rounded flex items-center justify-center" title="YouTube">
              <Play className="h-4 w-4 text-white fill-white" />
            </div>
            {/* Twitch */}
            <div className="w-8 h-8 bg-purple-600 rounded flex items-center justify-center" title="Twitch">
              <div className="w-4 h-4 bg-white rounded-sm" />
            </div>
            {/* TikTok */}
            <div className="w-8 h-8 bg-black rounded flex items-center justify-center border border-gray-700" title="TikTok">
              <div className="w-3 h-4 bg-gradient-to-r from-pink-500 to-cyan-500 rounded-sm" />
            </div>
            {/* Instagram */}
            <div className="w-8 h-8 bg-gradient-to-tr from-purple-600 via-pink-500 to-orange-500 rounded-lg flex items-center justify-center" title="Instagram">
              <div className="w-4 h-4 border-2 border-white rounded-md" />
            </div>
            {/* Vimeo */}
            <div className="flex items-center gap-1.5 opacity-50">
              <div className="w-8 h-8 bg-gray-700 rounded flex items-center justify-center" title="Vimeo (bientôt)">
                <div className="w-3 h-3 bg-white rounded-full" />
              </div>
              <span className="text-xs text-gray-500">Vimeo bientôt</span>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}