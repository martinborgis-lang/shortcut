'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Scissors, Menu, X } from 'lucide-react';

export default function Navbar() {
  const [isScrolled, setIsScrolled] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 50);
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const scrollToSection = (sectionId: string) => {
    const element = document.getElementById(sectionId);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
      setIsMobileMenuOpen(false);
    }
  };

  return (
    <motion.nav
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        isScrolled
          ? 'backdrop-blur-md bg-zinc-950/80 border-b border-white/10'
          : 'bg-transparent'
      }`}
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      transition={{ duration: 0.6 }}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <motion.div
            className="flex items-center gap-2 cursor-pointer flex-shrink-0"
            whileHover={{ scale: 1.05 }}
            onClick={() => scrollToSection('hero')}
          >
            <div className="w-8 h-8 rounded-lg bg-gradient-to-r from-purple-600 to-cyan-500 flex items-center justify-center">
              <Scissors className="h-5 w-5 text-white" />
            </div>
            <span className="text-xl font-bold bg-gradient-to-r from-purple-400 to-cyan-400 bg-clip-text text-transparent">
              ShortCut
            </span>
          </motion.div>

          {/* Navigation Desktop - FIX: explicit gap instead of space-x */}
          <div className="hidden md:flex items-center gap-10">
            <button
              onClick={() => scrollToSection('features')}
              className="text-sm text-gray-300 hover:text-white transition-colors duration-200 whitespace-nowrap"
            >
              Fonctionnalités
            </button>
            <button
              onClick={() => scrollToSection('pricing')}
              className="text-sm text-gray-300 hover:text-white transition-colors duration-200 whitespace-nowrap"
            >
              Tarifs
            </button>
            <button
              onClick={() => scrollToSection('faq')}
              className="text-sm text-gray-300 hover:text-white transition-colors duration-200 whitespace-nowrap"
            >
              FAQ
            </button>
          </div>

          {/* CTA Buttons Desktop */}
          <div className="hidden md:flex items-center gap-4 flex-shrink-0">
            <button className="text-sm text-gray-300 hover:text-white transition-colors duration-200">
              Connexion
            </button>
            <motion.button
              className="px-5 py-2 rounded-full bg-gradient-to-r from-purple-600 to-cyan-500 text-white text-sm font-medium hover:shadow-lg hover:shadow-purple-500/25 transition-all duration-200"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              Essai gratuit
            </motion.button>
          </div>

          {/* Menu Mobile */}
          <div className="md:hidden">
            <button
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              className="text-gray-300 hover:text-white transition-colors duration-200"
            >
              {isMobileMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
            </button>
          </div>
        </div>

        {/* Menu Mobile Dropdown */}
        {isMobileMenuOpen && (
          <motion.div
            className="md:hidden mt-4 pb-4 border-t border-white/10"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
          >
            <div className="flex flex-col gap-4 pt-4">
              <button
                onClick={() => scrollToSection('features')}
                className="text-gray-300 hover:text-white transition-colors duration-200 text-left"
              >
                Fonctionnalités
              </button>
              <button
                onClick={() => scrollToSection('pricing')}
                className="text-gray-300 hover:text-white transition-colors duration-200 text-left"
              >
                Tarifs
              </button>
              <button
                onClick={() => scrollToSection('faq')}
                className="text-gray-300 hover:text-white transition-colors duration-200 text-left"
              >
                FAQ
              </button>
              <hr className="border-white/10" />
              <button className="text-gray-300 hover:text-white transition-colors duration-200 text-left">
                Connexion
              </button>
              <motion.button
                className="px-5 py-2 rounded-full bg-gradient-to-r from-purple-600 to-cyan-500 text-white font-medium w-fit"
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                Essai gratuit
              </motion.button>
            </div>
          </motion.div>
        )}
      </div>
    </motion.nav>
  );
}