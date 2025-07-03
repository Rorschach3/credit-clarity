
import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom';
import { AnimatePresence } from 'framer-motion';
import { useTheme } from './hooks/use-theme';
import { Navbar } from './components/layout/Navbar';
import HomePage from "@/pages/HomePage";
import Dashboard from "@/pages/DashboardPage";
import AboutPage from "@/pages/AboutPage";
import LoginPage from "@/pages/LoginPage";
import SignupPage from "@/pages/SignupPage";
import ForgotPasswordPage from "@/pages/ForgotPasswordPage";
import ResetPasswordPage from '@/pages/ResetPasswordPage'; 
import ProfilePage from '@/pages/ProfilePage';
import Hero from './components/Hero/Hero';
import { AuthProvider, useAuth } from './hooks/use-auth';
import TradelinesPage from "@/pages/TradelinesPage";
import ServicesGrid from './components/Services/ServicesGrid';
import ProcessTimeline from './components/Process/ProcessTimeline';
import CreditReportUploadPage from './pages/CreditReportUploadPage';
import DisputeWizardPage from './pages/DisputeWizardPage';
import DisputeLetterPage from './pages/DisputeLetterPage';
import ContactForm from './components/Contact/ContactForm';
import Footer from './components/Footer/Footer';

function App() {
  return (
    <AuthProvider>
      <Router>
        <AppContent />
      </Router>
    </AuthProvider>
  );
}

function AppContent() {
  const { theme } = useTheme();
  const { isLoading } = useAuth();
  const location = useLocation();

  useEffect(() => {
    document.documentElement.classList.remove('light', 'dark');
    document.documentElement.classList.add(theme);
  }, [theme]);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background text-foreground flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  const routeKey = location.pathname || '/';

  return (
    <div className="min-h-screen bg-background text-foreground transition-colors duration-300">
      <Navbar />
      <main>
        <AnimatePresence mode="wait">
          <Routes location={location} key={routeKey}>
            <Route path="/" element={
              <>
                <Hero />
                <ServicesGrid />
                <ProcessTimeline />                 
                <ContactForm />
              </>
            } />
            <Route path="/home" element={<HomePage />} />
            <Route path="/signup" element={<SignupPage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/forgot-password" element={<ForgotPasswordPage />} />
            <Route path="/reset-password" element={<ResetPasswordPage />} />
            <Route path="/profile" element={<ProfilePage />} />
            <Route path="/about" element={<AboutPage />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/credit-report-upload" element={<CreditReportUploadPage />} />
            <Route path="/dispute-letter" element={<DisputeLetterPage />} />
            <Route path="/dispute-wizard" element={<DisputeWizardPage />} />
            <Route path="/tradelines" element={<TradelinesPage />} />
          </Routes>
        </AnimatePresence>
      </main>
      <Footer />
    </div>
  );
}

export default App;
