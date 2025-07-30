import React from 'react';
import { motion } from 'framer-motion';

interface ServiceCardProps {
  title: string;
  description: string;
  icon: React.ReactNode; // For minimal iconography
}

const ServiceCard: React.FC<ServiceCardProps> = ({ title, description, icon }) => {
  return (
    <motion.div
      whileHover={{ scale: 1.03, borderColor: 'var(--accent)' }}
      className="flex flex-col items-center rounded-lg border border-border bg-card p-6 text-center shadow-sm transition-all duration-300"
    >
      <div className="mb-4 text-4xl text-primary">{icon}</div>
      <h3 className="mb-2 text-2xl font-semibold text-foreground">{title}</h3>
      <p className="text-muted-foreground">{description}</p>
    </motion.div>
  );
};

export default ServiceCard;