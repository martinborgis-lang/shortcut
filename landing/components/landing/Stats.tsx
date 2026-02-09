'use client';

import { useEffect, useRef, useState } from 'react';
import { motion, useInView } from 'framer-motion';

const stats = [
  { label: 'Plus rapide que le montage manuel', value: 10, suffix: 'x' },
  { label: 'De temps gagné par vidéo', value: 90, suffix: '%' },
  { label: 'Créateurs actifs', value: 2000, suffix: '+', separator: true },
  { label: 'Shorts générés', value: 50000, suffix: '+', separator: true },
];

function AnimatedCounter({
  value,
  suffix,
  inView,
  separator,
}: {
  value: number;
  suffix: string;
  inView: boolean;
  separator?: boolean;
}) {
  const [count, setCount] = useState(0);

  useEffect(() => {
    if (!inView) return;

    let startTime: number | undefined;
    const duration = 2000;

    const animate = (currentTime: number) => {
      if (startTime === undefined) startTime = currentTime;
      const progress = Math.min((currentTime - startTime) / duration, 1);
      const easeOutQuart = 1 - Math.pow(1 - progress, 4);
      setCount(Math.floor(easeOutQuart * value));

      if (progress < 1) {
        requestAnimationFrame(animate);
      }
    };

    requestAnimationFrame(animate);
  }, [inView, value]);

  const display = separator ? count.toLocaleString('fr-FR') : count.toString();

  return (
    <span className="text-4xl sm:text-5xl md:text-6xl font-extrabold bg-gradient-to-r from-purple-400 to-cyan-400 bg-clip-text text-transparent">
      {display}
      {suffix}
    </span>
  );
}

export default function Stats() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true });

  return (
    <section ref={ref} className="py-24">
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
            Des résultats qui parlent{' '}
            <span className="bg-gradient-to-r from-purple-400 to-cyan-400 bg-clip-text text-transparent">
              d&apos;eux-mêmes
            </span>
          </h2>
          <p className="text-lg text-gray-400">
            Nos utilisateurs voient des résultats immédiats et mesurables.
          </p>
        </motion.div>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
          {stats.map((stat, index) => (
            <motion.div
              key={stat.label}
              className="text-center p-6 rounded-2xl bg-white/[0.03] border border-white/10 hover:bg-white/[0.06] transition-all duration-300"
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6, delay: index * 0.1 }}
            >
              <div className="mb-3">
                <AnimatedCounter
                  value={stat.value}
                  suffix={stat.suffix}
                  inView={isInView}
                  separator={stat.separator}
                />
              </div>
              <p className="text-gray-400 text-sm font-medium">{stat.label}</p>
            </motion.div>
          ))}
        </div>

        {/* Decorative line */}
        <motion.div
          className="mt-12 text-center"
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 1, delay: 0.5 }}
        >
          <div className="inline-flex items-center gap-4 text-gray-500">
            <div className="w-16 h-px bg-gradient-to-r from-transparent to-purple-500" />
            <span className="text-xs font-medium">Mis à jour en temps réel</span>
            <div className="w-16 h-px bg-gradient-to-l from-transparent to-cyan-500" />
          </div>
        </motion.div>
      </div>
    </section>
  );
}