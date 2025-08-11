import React, { Suspense, LazyExoticComponent } from 'react';
import { ErrorBoundary } from 'react-error-boundary';

// Loading component for lazy loaded components
const LoadingSpinner = ({ message = "Loading..." }: { message?: string }) => (
  <div className="flex items-center justify-center min-h-[200px]">
    <div className="flex flex-col items-center space-y-4">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      <p className="text-sm text-gray-600">{message}</p>
    </div>
  </div>
);

// Error fallback component
const ErrorFallback = ({ error, resetErrorBoundary }: { error: Error; resetErrorBoundary: () => void }) => (
  <div className="flex items-center justify-center min-h-[200px]">
    <div className="text-center">
      <h3 className="text-lg font-medium text-gray-900 mb-2">Something went wrong</h3>
      <p className="text-sm text-gray-600 mb-4">{error.message}</p>
      <button 
        onClick={resetErrorBoundary}
        className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
      >
        Try again
      </button>
    </div>
  </div>
);

interface LazyLoadWrapperProps {
  children: React.ReactNode;
  loadingMessage?: string;
  fallbackComponent?: React.ComponentType<any>;
}

/**
 * Wrapper for lazy-loaded components with error boundary and loading states
 */
export const LazyLoadWrapper: React.FC<LazyLoadWrapperProps> = ({
  children,
  loadingMessage,
  fallbackComponent: FallbackComponent,
}) => {
  return (
    <ErrorBoundary 
      FallbackComponent={FallbackComponent || ErrorFallback}
      onError={(error) => {
        console.error('Lazy component loading error:', error);
        // You could send this to an error tracking service
      }}
    >
      <Suspense fallback={<LoadingSpinner message={loadingMessage} />}>
        {children}
      </Suspense>
    </ErrorBoundary>
  );
};

/**
 * Higher-order component for creating lazy-loaded components with built-in error handling
 */
export function withLazyLoading<P extends object>(
  Component: LazyExoticComponent<React.ComponentType<P>>,
  options: {
    loadingMessage?: string;
    fallbackComponent?: React.ComponentType<any>;
  } = {}
) {
  return function LazyComponent(props: P) {
    return (
      <LazyLoadWrapper 
        loadingMessage={options.loadingMessage}
        fallbackComponent={options.fallbackComponent}
      >
        <Component {...props} />
      </LazyLoadWrapper>
    );
  };
}

// Pre-configured lazy loading wrappers for different component types
export const LazyPageWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <LazyLoadWrapper loadingMessage="Loading page...">
    {children}
  </LazyLoadWrapper>
);

export const LazyModalWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <LazyLoadWrapper loadingMessage="Loading modal...">
    {children}
  </LazyLoadWrapper>
);

export const LazyChartWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <LazyLoadWrapper loadingMessage="Loading chart...">
    {children}
  </LazyLoadWrapper>
);