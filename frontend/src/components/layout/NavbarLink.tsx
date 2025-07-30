import React from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';

interface NavbarLinkProps {
  to: string;
  label: string;
}

const NavbarLink: React.FC<NavbarLinkProps> = ({ to, label }) => {
  return (
    <motion.div
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
      className="relative group"
    >
      <Link
        to={`/${to === 'home' ? '' : to}`}
        className="text-foreground hover:text-primary-foreground transition-colors duration-200 text-lg font-medium"
      >
        {label}
      </Link>
      <motion.span
        className="absolute bottom-0 left-0 w-full h-0.5 bg-primary-foreground origin-left scale-x-0 group-hover:scale-x-100 transition-transform duration-300"
        layoutId="underline"
      />
    </motion.div>
  );
};

export default NavbarLink;