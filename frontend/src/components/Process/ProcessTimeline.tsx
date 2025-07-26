import React from 'react';
import { motion } from 'framer-motion';

interface ProcessStepProps {
  step: number;
  title: string;
  description: string;
}

const ProcessStep: React.FC<ProcessStepProps> = ({ step, title, description }) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 50 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, amount: 0.5 }}
      transition={{ duration: 0.6, ease: 'easeOut' }}
      className="relative flex items-start md:items-center md:flex-row flex-col mb-8 last:mb-0"
    >
      <div className="flex-shrink-0 w-12 h-12 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-xl font-bold z-10 md:mr-6 mb-4 md:mb-0">
        {step}
      </div>
      <div className="flex-grow">
        <h3 className="text-2xl font-bold text-foreground mb-2">{title}</h3>
        <p className="text-muted-foreground">{description}</p>
      </div>
      {step < 4 && ( // Assuming 4 steps, adjust as needed
        <div className="absolute left-6 top-12 h-[calc(100%-3rem)] w-0.5 bg-border md:hidden" />
      )}
    </motion.div>
  );
};

const processSteps = [
  {
    step: 1,
    title: 'Initial Consultation & Analysis',
    description: 'We begin with a free consultation to understand your financial goals and analyze your credit reports for inaccuracies.',
  },
  {
    step: 2,
    title: 'Strategic Dispute Preparation',
    description: 'Our experts craft personalized dispute letters targeting negative items, backed by relevant credit laws.',
  },
  {
    step: 3,
    title: 'Active Communication & Follow-Up',
    description: 'We handle all correspondence with credit bureaus and creditors, ensuring timely and effective communication.',
  },
  {
    step: 4,
    title: 'Credit Building & Monitoring',
    description: 'Receive ongoing guidance to build positive credit, along with monitoring to track your progress and maintain a healthy score.',
  },
];

const ProcessTimeline: React.FC = () => {
  return (
    <section id="process" className="bg-accent py-20">
      <div className="container mx-auto px-4 text-center">
        <motion.h2
          initial={{ opacity: 0, y: 50 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, amount: 0.3 }}
          transition={{ duration: 0.8, ease: 'easeOut' }}
          className="mb-12 text-4xl font-bold text-foreground"
        >
          Our Proven Credit Repair Process
        </motion.h2>
        <div className="relative flex flex-col items-center md:flex-row md:justify-between md:space-x-8">
          {/* Horizontal line for desktop */}
          <div className="absolute hidden md:block top-6 left-0 right-0 h-0.5 bg-border z-0" />
          {processSteps.map((step, index) => (
            <ProcessStep key={index} {...step} />
          ))}
        </div>
      </div>
    </section>
  );
};

export default ProcessTimeline;