
import React, { useEffect, Suspense } from 'react';
import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom';
import { QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { AnimatePresence } from 'framer-motion';
import { useTheme } from './hooks/use-theme';
import { Navbar } from './components/layout/Navbar';
import { ErrorBoundary } from './components/ErrorBoundary';
import { queryClient } from './lib/react-query';
import { 
  PageLoading, 
  DisputeWizardLoading, 
  CreditReportUploadLoading, 
  TradelinesLoading, 
  ProfileLoading,
  DashboardLoading 
} from './components/ui/loading';

// Eager load lightweight pages
import HomePage from "@/pages/HomePage";
import AboutPage from "@/pages/AboutPage";
import LoginPage from "@/pages/LoginPage";
import SignupPage from "@/pages/SignupPage";
import ForgotPasswordPage from "@/pages/ForgotPasswordPage";
import ResetPasswordPage from '@/pages/ResetPasswordPage';
import DisputeLetterPage from './pages/DisputeLetterPage';
import FaqPage from './pages/FaqPage';
import PricingPage from './pages/PricingPage';
import BlogPage from './pages/BlogPage';

// Lazy load heavy pages for code splitting
const ProfilePage = React.lazy(() => import('@/pages/ProfilePage'));
const Dashboard = React.lazy(() => import('@/pages/DashboardPage'));
const TradelinesPage = React.lazy(() => import('@/pages/TradelinesPage'));
const CreditReportUploadPage = React.lazy(() => import('./pages/CreditReportUploadPage'));
const DisputeWizardPage = React.lazy(() => import('./pages/DisputeWizardPage'));

// Lazy load component chunks
const Hero = React.lazy(() => import('./components/Hero/Hero'));
const ServicesGrid = React.lazy(() => import('./components/Services/ServicesGrid'));
const ProcessTimeline = React.lazy(() => import('./components/Process/ProcessTimeline'));
const ContactForm = React.lazy(() => import('./components/Contact/ContactForm'));
const Footer = React.lazy(() => import('./components/Footer/Footer'));

import { AuthProvider, useAuth } from './hooks/use-auth';

function App() {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <Router>
            <AppContent />
          </Router>
        </AuthProvider>
        {/* React Query DevTools - only shows in development */}
        <ReactQueryDevtools initialIsOpen={false} />
      </QueryClientProvider>
    </ErrorBoundary>
  );
}

function AppContent() {
  const { theme } = useTheme();
  const { isLoading } = useAuth();
  const location = useLocation();

  useEffect(() => {
    document.documentElement.classList.remove('light', 'dark');
    document.documentElement.classList.add(theme ?? 'dark');
  }, [theme]);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background text-foreground flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  const routeKey = location.pathname + location.search;

  return (
    <div className="min-h-screen bg-background text-foreground transition-colors duration-300">
      <Navbar />
      <main>
        <AnimatePresence mode="wait">
          <Routes location={location} key={routeKey}>
            <Route path="/" element={
              <Suspense fallback={<PageLoading message="Loading homepage..." />}>
                <Hero />
                <ServicesGrid />
                <ProcessTimeline />                 
                <ContactForm />
              </Suspense>
            } />
            <Route path="/home" element={<HomePage />} />
            <Route path="/signup" element={<SignupPage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/forgot-password" element={<ForgotPasswordPage />} />
            <Route path="/reset-password" element={<ResetPasswordPage />} />
            <Route path="/profile" element={
              <Suspense fallback={<ProfileLoading />}>
                <ProfilePage />
              </Suspense>
            } />
            <Route path="/about" element={<AboutPage />} />
            <Route path="/dashboard" element={
              <Suspense fallback={<DashboardLoading />}>
                <Dashboard />
              </Suspense>
            } />
            <Route path="/credit-report-upload" element={
              <Suspense fallback={<CreditReportUploadLoading />}>
                <CreditReportUploadPage />
              </Suspense>
            } />
            <Route path="/dispute-letter" element={<DisputeLetterPage />} />
            <Route path="/dispute-wizard" element={
              <Suspense fallback={<DisputeWizardLoading />}>
                <DisputeWizardPage />
              </Suspense>
            } />
            <Route path="/tradelines" element={
              <Suspense fallback={<TradelinesLoading />}>
                <TradelinesPage />
              </Suspense>
            } />
            <Route path="/contact" element={
              <Suspense fallback={<PageLoading message="Loading contact form..." />}>
                <ContactForm />
              </Suspense>
            } />
            <Route path="/faq" element={<FaqPage />} />
            <Route path="/pricing" element={<PricingPage />} />
            <Route path="/blog" element={<BlogPage />} />
          </Routes>
        </AnimatePresence>
      </main>
      <Suspense fallback={<div />}>
        <Footer />
      </Suspense>
    </div>
  );
}

export default App;
