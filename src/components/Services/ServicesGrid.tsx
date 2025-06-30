
import React from 'react';
import { motion, Variants } from 'framer-motion';
import ServiceCard from './ServiceCard';
import { FileText, BarChart3, Shield, Clock } from 'lucide-react';

const services = [
  {
    icon: FileText,
    title: "AI Credit Analysis",
    description: "Advanced artificial intelligence scans your credit report to identify errors and opportunities for improvement."
  },
  {
    icon: BarChart3,
    title: "Dispute Letter Generation",
    description: "Automatically generate professional dispute letters tailored to your specific credit issues."
  },
  {
    icon: Shield,
    title: "Credit Monitoring",
    description: "Continuous monitoring of your credit reports with real-time alerts for any changes or updates."
  },
  {
    icon: Clock,
    title: "Progress Tracking",
    description: "Track the status of your disputes and monitor improvements to your credit score over time."
  }
];

const ServicesGrid = () => {
  const containerVariants: Variants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.2
      }
    }
  };

  const itemVariants: Variants = {
    hidden: { opacity: 0, y: 20 },
    show: { 
      opacity: 1, 
      y: 0,
      transition: { 
        duration: 0.6,
        ease: [0.4, 0.0, 0.2, 1]
      }
    }
  };

  return (
    <section className="py-20 bg-gray-50 dark:bg-gray-900">
      <div className="container mx-auto px-4">
        <motion.div
          initial="hidden"
          whileInView="show"
          viewport={{ once: true, amount: 0.3 }}
          variants={containerVariants}
          className="text-center mb-16"
        >
          <motion.h2 
            variants={itemVariants}
            className="text-4xl md:text-5xl font-bold text-gray-900 dark:text-white mb-6"
          >
            Our Services
          </motion.h2>
          <motion.p 
            variants={itemVariants}
            className="text-xl text-gray-600 dark:text-gray-300 max-w-3xl mx-auto"
          >
            Comprehensive credit repair solutions powered by artificial intelligence
          </motion.p>
        </motion.div>

        <motion.div
          variants={containerVariants}
          initial="hidden"
          whileInView="show"
          viewport={{ once: true, amount: 0.2 }}
          className="grid md:grid-cols-2 lg:grid-cols-4 gap-8"
        >
          {services.map((service, index) => (
            <motion.div key={index} variants={itemVariants}>
              <ServiceCard 
                icon={React.createElement(service.icon, { className: "h-8 w-8" })}
                title={service.title}
                description={service.description}
              />
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
};

export default ServicesGrid;
