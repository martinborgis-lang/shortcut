'use client';

import { Scissors, Twitter, Hash, Play, MessageCircle } from 'lucide-react';

const footerLinks = {
  product: [
    { name: 'Fonctionnalités', href: '#features' },
    { name: 'Tarifs', href: '#pricing' },
    { name: 'FAQ', href: '#faq' },
    { name: 'Roadmap', href: '#' },
  ],
  resources: [
    { name: 'Blog', href: '#' },
    { name: "Centre d'aide", href: '#' },
    { name: 'API Docs', href: '#' },
    { name: 'Statut', href: '#' },
  ],
  legal: [
    { name: 'CGU', href: '#' },
    { name: 'Politique de confidentialité', href: '#' },
    { name: 'Mentions légales', href: '#' },
    { name: 'Cookies', href: '#' },
  ],
};

const socialLinks = [
  { name: 'Twitter', icon: Twitter, href: '#' },
  { name: 'TikTok', icon: Hash, href: '#' },
  { name: 'YouTube', icon: Play, href: '#' },
  { name: 'Discord', icon: MessageCircle, href: '#' },
];

export default function Footer() {
  const scrollToSection = (href: string) => {
    if (href.startsWith('#') && href.length > 1) {
      const element = document.getElementById(href.substring(1));
      if (element) {
        element.scrollIntoView({ behavior: 'smooth' });
      }
    }
  };

  return (
    <footer className="border-t border-white/10 bg-zinc-950">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-8 lg:gap-12">
          {/* Logo & Description */}
          <div className="col-span-2 md:col-span-4 lg:col-span-2">
            <div className="flex items-center gap-2 mb-4">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-r from-purple-600 to-cyan-500 flex items-center justify-center">
                <Scissors className="h-5 w-5 text-white" />
              </div>
              <span className="text-xl font-bold bg-gradient-to-r from-purple-400 to-cyan-400 bg-clip-text text-transparent">
                ShortCut
              </span>
            </div>
            <p className="text-gray-400 text-sm mb-6 max-w-xs leading-relaxed">
              L&apos;IA qui transforme vos vidéos en shorts viraux. Créez 10x plus
              vite, publiez 10x plus, générez 10x plus de vues.
            </p>
            <div className="flex items-center gap-3">
              {socialLinks.map((social) => {
                const Icon = social.icon;
                return (
                  <a
                    key={social.name}
                    href={social.href}
                    className="w-9 h-9 rounded-full bg-white/[0.08] flex items-center justify-center text-gray-400 hover:text-white hover:bg-white/[0.15] transition-all duration-200"
                  >
                    <Icon className="h-4 w-4" />
                  </a>
                );
              })}
            </div>
          </div>

          {/* Product Links */}
          <div>
            <h3 className="text-white text-sm font-semibold mb-4">Produit</h3>
            <ul className="space-y-2.5">
              {footerLinks.product.map((link) => (
                <li key={link.name}>
                  <button
                    onClick={() => scrollToSection(link.href)}
                    className="text-gray-400 hover:text-white transition-colors duration-200 text-sm"
                  >
                    {link.name}
                  </button>
                </li>
              ))}
            </ul>
          </div>

          {/* Resources Links */}
          <div>
            <h3 className="text-white text-sm font-semibold mb-4">Ressources</h3>
            <ul className="space-y-2.5">
              {footerLinks.resources.map((link) => (
                <li key={link.name}>
                  <a
                    href={link.href}
                    className="text-gray-400 hover:text-white transition-colors duration-200 text-sm"
                  >
                    {link.name}
                  </a>
                </li>
              ))}
            </ul>
          </div>

          {/* Legal Links */}
          <div>
            <h3 className="text-white text-sm font-semibold mb-4">Légal</h3>
            <ul className="space-y-2.5">
              {footerLinks.legal.map((link) => (
                <li key={link.name}>
                  <a
                    href={link.href}
                    className="text-gray-400 hover:text-white transition-colors duration-200 text-sm"
                  >
                    {link.name}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="mt-14 pt-8 border-t border-white/10 flex flex-col sm:flex-row justify-between items-center gap-4">
          <p className="text-gray-500 text-sm">
            © 2025 ShortCut. Tous droits réservés.
          </p>
          <div className="flex items-center gap-4 text-sm text-gray-500">
            <span>Fait avec ❤️ en France</span>
            <div className="flex items-center gap-1.5">
              <div className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse" />
              <span>Tous systèmes opérationnels</span>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
}