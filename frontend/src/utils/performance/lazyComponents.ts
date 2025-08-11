/**
 * Centralized lazy component imports for better performance
 * Split components by usage patterns and importance
 */
import { lazy } from 'react';

// Critical path components (loaded immediately)
// These should NOT be lazy loaded as they're needed on first render

// Page components (lazy loaded)
export const LazyDashboardPage = lazy(() => import('@/pages/DashboardPage'));
export const LazyCreditReportUploadPage = lazy(() => import('@/pages/CreditReportUploadPage'));
export const LazyDisputeWizardPage = lazy(() => import('@/pages/DisputeWizardPage'));
export const LazyTradelinesPage = lazy(() => import('@/pages/TradelinesPage'));
export const LazyProfilePage = lazy(() => import('@/pages/ProfilePage'));
export const LazyAdminPage = lazy(() => import('@/pages/AdminPage'));
export const LazyDebugPage = lazy(() => import('@/pages/DebugPage'));

// Heavy components (lazy loaded)
export const LazyCreditReportViewer = lazy(() => import('@/components/CreditReportViewer'));
export const LazyPDFDebugger = lazy(() => import('@/components/debug/PDFDebugger'));
export const LazyTradelineEditor = lazy(() => import('@/components/credit-upload/TradelineEditor'));

// Chart components (heavy libraries)
export const LazyCreditScoreCard = lazy(() => import('@/components/dashboard/CreditScoreCard'));
export const LazyCreditScoreProgress = lazy(() => import('@/components/dashboard/CreditScoreProgress'));

// AI and processing components
export const LazyAIAnalysisResults = lazy(() => import('@/components/credit-upload/AIAnalysisResults'));
export const LazyEnhancedDocumentScanner = lazy(() => import('@/components/document/EnhancedDocumentScanner'));

// Admin components (rarely used)
export const LazyUserManagement = lazy(() => import('@/components/admin/UserManagement'));
export const LazyAuditLog = lazy(() => import('@/components/admin/AuditLog'));
export const LazyRealTimeQueue = lazy(() => import('@/components/admin/RealTimeQueue'));

// Dispute letter components
export const LazyDisputeLetterGenerator = lazy(() => import('@/components/disputes/DisputeLetterGenerator'));
export const LazyAIDisputeLetterGenerator = lazy(() => import('@/components/disputes/AIDisputeLetterGenerator'));
export const LazyDisputePacketBuilder = lazy(() => import('@/components/disputes/DisputePacketBuilder'));

// Complex form components
export const LazyManualTradelineModal = lazy(() => import('@/components/disputes/ManualTradelineModal'));
export const LazyPersonalInfoForm = lazy(() => import('@/components/disputes/PersonalInfoForm'));

// Utility function to create preloader
export function preloadComponent(componentLoader: () => Promise<any>) {
  const componentImport = componentLoader();
  return componentImport;
}

// Preload critical components that might be needed soon
export function preloadCriticalComponents() {
  // Preload dashboard and upload page as they're commonly accessed
  setTimeout(() => {
    preloadComponent(() => import('@/pages/DashboardPage'));
    preloadComponent(() => import('@/pages/CreditReportUploadPage'));
  }, 1000);
}

// Component groups for batch preloading
export const COMPONENT_GROUPS = {
  dashboard: [
    () => import('@/pages/DashboardPage'),
    () => import('@/components/dashboard/CreditScoreCard'),
    () => import('@/components/dashboard/CreditScoreProgress'),
  ],
  
  upload: [
    () => import('@/pages/CreditReportUploadPage'),
    () => import('@/components/credit-upload/TradelineEditor'),
    () => import('@/components/credit-upload/AIAnalysisResults'),
  ],
  
  disputes: [
    () => import('@/pages/DisputeWizardPage'),
    () => import('@/components/disputes/DisputeLetterGenerator'),
    () => import('@/components/disputes/AIDisputeLetterGenerator'),
  ],
  
  admin: [
    () => import('@/pages/AdminPage'),
    () => import('@/components/admin/UserManagement'),
    () => import('@/components/admin/AuditLog'),
  ],
  
  debug: [
    () => import('@/pages/DebugPage'),
    () => import('@/components/debug/PDFDebugger'),
  ]
};

// Batch preload functions
export function preloadComponentGroup(groupName: keyof typeof COMPONENT_GROUPS) {
  const group = COMPONENT_GROUPS[groupName];
  if (group) {
    group.forEach(loader => {
      setTimeout(() => loader(), Math.random() * 2000); // Stagger loading
    });
  }
}

// Route-based preloading
export function preloadRouteComponents(currentRoute: string) {
  switch (currentRoute) {
    case '/':
    case '/dashboard':
      preloadComponentGroup('upload'); // Preload upload page from dashboard
      break;
      
    case '/upload':
      preloadComponentGroup('disputes'); // Preload disputes after upload
      break;
      
    case '/disputes':
      preloadComponentGroup('dashboard'); // Preload dashboard from disputes
      break;
      
    case '/admin':
      preloadComponentGroup('debug'); // Preload debug tools for admins
      break;
  }
}

// Hook for component preloading
export function useComponentPreloading(currentRoute: string) {
  React.useEffect(() => {
    // Preload critical components on app start
    preloadCriticalComponents();
    
    // Preload route-specific components
    const timer = setTimeout(() => {
      preloadRouteComponents(currentRoute);
    }, 2000);
    
    return () => clearTimeout(timer);
  }, [currentRoute]);
}

// Performance monitoring for lazy components
let componentLoadTimes: Record<string, number> = {};

export function trackComponentLoadTime(componentName: string, startTime: number) {
  const loadTime = Date.now() - startTime;
  componentLoadTimes[componentName] = loadTime;
  
  // Log slow loading components
  if (loadTime > 1000) {
    console.warn(`Slow component load: ${componentName} took ${loadTime}ms`);
  }
  
  // Send to analytics if available
  if (window.gtag) {
    window.gtag('event', 'component_load_time', {
      component_name: componentName,
      load_time: loadTime
    });
  }
}

export function getComponentLoadStats() {
  return { ...componentLoadTimes };
}

// Clear stats
export function clearComponentLoadStats() {
  componentLoadTimes = {};
}