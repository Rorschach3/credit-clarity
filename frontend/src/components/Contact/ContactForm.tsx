import React from 'react';
import { motion, easeOut } from 'framer-motion';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { contactFormSchema, ContactFormInputs } from '@/lib/validation/contactFormSchema';

const ContactForm: React.FC = () => {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    reset,
  } = useForm<ContactFormInputs>({
    resolver: zodResolver(contactFormSchema),
  });

  const onSubmit = async (data: ContactFormInputs) => {
    console.log(data);
    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 1000));
    alert('Message sent successfully!');
    reset();
  };

  const fadeInAnimation = {
    initial: { opacity: 0, y: 50 },
    whileInView: { opacity: 1, y: 0 },
    viewport: { once: true, amount: 0.3 },
    transition: { duration: 0.8, ease: easeOut },
  };

  return (
    <section id="contact" className="bg-background py-20">
      <div className="container mx-auto px-4 text-center">
        <motion.h2
          {...fadeInAnimation}
          className="mb-12 text-4xl font-bold text-foreground"
        >
          Get In Touch
        </motion.h2>
        <motion.form
          {...fadeInAnimation}
          className="mx-auto max-w-lg rounded-lg border border-border bg-card p-8 shadow-lg"
          onSubmit={handleSubmit(onSubmit)}
        >
          <div className="mb-4 text-left">
            <label htmlFor="name" className="mb-2 block text-sm font-medium text-foreground">
              Name
            </label>
            <input
              type="text"
              id="name"
              {...register('name')}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-foreground focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
            />
            {errors.name && <p className="mt-1 text-sm text-destructive">{errors.name.message}</p>}
          </div>

          <div className="mb-4 text-left">
            <label htmlFor="email" className="mb-2 block text-sm font-medium text-foreground">
              Email
            </label>
            <input
              type="email"
              id="email"
              {...register('email')}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-foreground focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
            />
            {errors.email && <p className="mt-1 text-sm text-destructive">{errors.email.message}</p>}
          </div>

          <div className="mb-4 text-left">
            <label htmlFor="phone" className="mb-2 block text-sm font-medium text-foreground">
              Phone (Optional)
            </label>
            <input
              type="text"
              id="phone"
              {...register('phone')}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-foreground focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
            />
          </div>

          <div className="mb-6 text-left">
            <label htmlFor="message" className="mb-2 block text-sm font-medium text-foreground">
              Message
            </label>
            <textarea
              id="message"
              rows={5}
              {...register('message')}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-foreground focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
            ></textarea>
            {errors.message && <p className="mt-1 text-sm text-destructive">{errors.message.message}</p>}
          </div>

          <motion.button
            type="submit"
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            disabled={isSubmitting}
            className="rounded-full bg-primary px-8 py-3 text-lg font-semibold text-primary-foreground shadow-lg transition-all duration-300 hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSubmitting ? 'Sending...' : 'Send Message'}
          </motion.button>
        </motion.form>
      </div>
    </section>
  );
};

export default ContactForm;