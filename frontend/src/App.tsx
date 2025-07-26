import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider } from './components/theme-provider';
import { Toaster } from './components/ui/toaster';
import { AuthProvider, useAuth } from './hooks/use-auth';
import MainLayout from './components/layout/MainLayout';
import AdminRoute from './components/auth/AdminRoute.tsx';
import Dashboard from './pages/DashboardPage';
import HomePage from './pages/HomePage';
import LoginPage from './pages/LoginPage';
import SignupPage from './pages/SignupPage';
import ForgotPasswordPage from './pages/ForgotPasswordPage';
import ResetPasswordPage from './pages/ResetPasswordPage';
import AboutPage from './pages/AboutPage';
import ContactPage from './pages/ContactPage';
import FaqPage from './pages/FaqPage';
import PricingPage from './pages/PricingPage';
import FeaturesPage from './pages/FeaturesPage';
import TestimonialsPage from './pages/TestimonialsPage';
import DisputesPage from './pages/DisputesPage';
import TradelinesPage from './pages/TradelinesPage';
import AdminPage from './pages/AdminPage';
import AdminDashboardPage from './pages/admin/AdminDashboardPage';
import ProfilePage from './pages/ProfilePage';
import BlogPage from './pages/BlogPage';
import DisputeWizardPage from './pages/DisputeWizardPage.tsx';
import NotFoundPage from './pages/NotFoundPage';
import { ParsedTradeline } from "@/utils/tradelineParser";

export default function App() {
  return (
    <AuthProvider>
        <InnerApp /> {/* ✅ Removed 'theme' prop */}
    </AuthProvider>
  );
}

function InnerApp() {
  const { isLoading } = useAuth();

  if (isLoading) {
    return <div>Loading...</div>;
  }

  return (
    <ThemeProvider
      attribute="class"
      defaultTheme="system" // can be "light", "dark", or "system"
      disableTransitionOnChange
    >
      <Router>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/home" element={<HomePage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/signup" element={<SignupPage />} />
          <Route path="/forgot-password" element={<ForgotPasswordPage />} />
          <Route path="/reset-password" element={<ResetPasswordPage />} />
          <Route path="/about" element={<AboutPage />} />
          <Route path="/contact" element={<ContactPage />} />
          <Route path="/faq" element={<FaqPage />} />
          <Route path="/pricing" element={<PricingPage />} />
          <Route path="/features" element={<FeaturesPage />} />
          <Route path="/testimonials" element={<TestimonialsPage />} />
          <Route path="/disputes" element={<DisputesPage />} />
          <Route path="/tradelines" element={<MainLayout><TradelinesPage /></MainLayout>} />
          <Route path="/dispute-wizard" element={<DisputeWizardPage />} />
          <Route
            path="/admin"
            element={
              <AdminRoute>
                <AdminPage />
              </AdminRoute>
            }
          />
          <Route path="/profile" element={<ProfilePage />} />
          <Route path="/blog" element={<BlogPage />} />

          <Route path="*" element={<NotFoundPage />} />

          <Route
            path="/admin/dashboard"
            element={
              <AdminRoute>
                <AdminDashboardPage />
              </AdminRoute>
            }
          />
        </Routes>
      </Router>
      <Toaster />
    </ThemeProvider>
  );
}
