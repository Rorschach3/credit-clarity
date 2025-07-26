import React from 'react';
import { motion } from 'framer-motion';

const Hero: React.FC = () => {
  return (
    <section id="home" className="relative flex min-h-screen items-center justify-center overflow-hidden bg-gradient-to-br from-background to-accent-foreground py-20 text-center">
      <div className="container z-10 px-4">
        <motion.h1
          initial={{ opacity: 0, y: 50 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: 'easeOut' }}
          className="mb-4 text-5xl font-bold leading-tight text-foreground md:text-6xl"
        >
          Credit Repair Services You Can Trust
        </motion.h1>
        <motion.p
          initial={{ opacity: 0, y: 50 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: 'easeOut', delay: 0.2 }}
          className="mb-8 text-xl text-muted-foreground md:text-2xl"
        >
          Raise your credit score. Reclaim your financial freedom.
        </motion.p>
        <motion.button
          initial={{ opacity: 0, y: 50 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: 'easeOut', delay: 0.4 }}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          className="rounded-full bg-primary px-8 py-3 text-lg font-semibold text-primary-foreground shadow-lg transition-all duration-300 hover:bg-primary/90"
        >
          Schedule Free Consultation
        </motion.button>
      </div>
    </section>
  );
};

export default Hero;