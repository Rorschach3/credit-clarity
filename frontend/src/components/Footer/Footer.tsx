import React from 'react';
import { FaPhone, FaEnvelope, FaFacebook, FaTwitter, FaLinkedin } from 'react-icons/fa'; // Example social icons

const Footer: React.FC = () => {
  return (
    <footer className="bg-card py-10 text-foreground">
      <div className="container mx-auto px-4 text-center">
        <div className="mb-6 flex flex-col items-center justify-center space-y-4 md:flex-row md:space-x-8 md:space-y-0">
          <div className="flex items-center">
            <FaPhone className="mr-2 text-primary" />
            <span className="text-sm text-muted-foreground">(123) 456-7890</span>
          </div>
          <div className="flex items-center">
            <FaEnvelope className="mr-2 text-primary" />
            <span className="text-sm text-muted-foreground">info@creditclarity.com</span>
          </div>
        </div>
        <div className="mb-6 flex justify-center space-x-6">
          <a href="#" className="text-muted-foreground hover:text-primary transition-colors duration-200">
            <FaFacebook size={24} />
          </a>
          <a href="#" className="text-muted-foreground hover:text-primary transition-colors duration-200">
            <FaTwitter size={24} />
          </a>
          <a href="#" className="text-muted-foreground hover:text-primary transition-colors duration-200">
            <FaLinkedin size={24} />
          </a>
        </div>
        <p className="text-xs text-muted-foreground">
          &copy; {new Date().getFullYear()} CreditClarity. All rights reserved.
        </p>
      </div>
    </footer>
  );
};

export default Footer;