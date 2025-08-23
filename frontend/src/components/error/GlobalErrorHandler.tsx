/**
 * Global Error Handler Provider
 * Wraps the entire app to catch and handle all types of errors
 */
import React, { createContext, useContext, useEffect, ReactNode } from 'react'
import { ErrorBoundary } from './ErrorBoundaryComponent'
import { useErrorBoundary } from '@/hooks/useErrorBoundary'
import { useMonitoring } from '@/hooks/useMonitoring'
import { toast } from 'sonner'

interface GlobalErrorContextType {
  captureError: (error: Error, component?: string, action?: string) => void
  reportError: (error: Error, context?: Record<string, any>) => void
}

const GlobalErrorContext = createContext<GlobalErrorContextType | null>(null)

export function useGlobalError() {
  const context = useContext(GlobalErrorContext)
  if (!context) {
    throw new Error('useGlobalError must be used within a GlobalErrorProvider')
  }
  return context
}

interface GlobalErrorProviderProps {
  children: ReactNode
  enableReporting?: boolean
  enableToasts?: boolean
}

export function GlobalErrorProvider({ 
  children, 
  enableReporting = true,
  enableToasts = true 
}: GlobalErrorProviderProps) {
  const { captureError } = useErrorBoundary({
    enableLogging: true,
    enableToasts,
    reportToService: enableReporting
  })
  
  const { trackError } = useMonitoring()

  // Global unhandled error handler
  useEffect(() => {
    const handleError = (event: ErrorEvent) => {
      const error = event.error || new Error(event.message)
      captureError(error, 'global', 'unhandled_error')
      trackError(error, {
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno,
        type: 'unhandled_error'
      })
    }

    const handleRejection = (event: PromiseRejectionEvent) => {
      const error = event.reason instanceof Error 
        ? event.reason 
        : new Error(String(event.reason))
      
      captureError(error, 'global', 'unhandled_promise_rejection')
      trackError(error, {
        type: 'unhandled_promise_rejection',
        reason: event.reason
      })
      
      // Prevent default browser behavior
      event.preventDefault()
    }

    // Resource loading errors
    const handleResourceError = (event: Event) => {
      const target = event.target as HTMLElement
      const error = new Error(`Failed to load resource: ${target.tagName}`)
      
      captureError(error, 'global', 'resource_load_error')
      trackError(error, {
        type: 'resource_load_error',
        tagName: target.tagName,
        src: (target as any).src || (target as any).href
      })
    }

    // Network errors
    const handleNetworkError = (event: Event) => {
      if (navigator.onLine === false) {
        const error = new Error('Network connection lost')
        captureError(error, 'global', 'network_error')
        
        if (enableToasts) {
          toast.error('Connection lost', {
            description: 'Please check your internet connection'
          })
        }
      }
    }

    // Register global error handlers
    window.addEventListener('error', handleError)
    window.addEventListener('unhandledrejection', handleRejection)
    window.addEventListener('error', handleResourceError, true) // Capture phase
    window.addEventListener('offline', handleNetworkError)

    return () => {
      window.removeEventListener('error', handleError)
      window.removeEventListener('unhandledrejection', handleRejection)
      window.removeEventListener('error', handleResourceError, true)
      window.removeEventListener('offline', handleNetworkError)
    }
  }, [captureError, trackError, enableToasts])

  // Console error interception (for development)
  useEffect(() => {
    if (process.env.NODE_ENV !== 'development') return

    const originalConsoleError = console.error
    console.error = (...args: any[]) => {
      // Call original console.error
      originalConsoleError.apply(console, args)
      
      // Track console errors
      const error = new Error(args.join(' '))
      trackError(error, {
        type: 'console_error',
        args: args.map(arg => String(arg))
      })
    }

    return () => {
      console.error = originalConsoleError
    }
  }, [trackError])

  const reportError = (error: Error, context?: Record<string, any>) => {
    captureError(error, 'manual', 'reported_error')
    trackError(error, {
      type: 'manual_report',
      ...context
    })
  }

  const contextValue: GlobalErrorContextType = {
    captureError,
    reportError
  }

  return (
    <GlobalErrorContext.Provider value={contextValue}>
      <ErrorBoundary 
        enableReporting={enableReporting}
        onError={(error, errorInfo) => {
          trackError(error, {
            type: 'react_error_boundary',
            componentStack: errorInfo.componentStack
          })
        }}
      >
        {children}
      </ErrorBoundary>
    </GlobalErrorContext.Provider>
  )
}

/**
 * Higher-order component for component-level error handling
 */
export function withGlobalErrorHandler<P extends object>(
  Component: React.ComponentType<P>,
  componentName?: string
) {
  const WrappedComponent = (props: P) => {
    const { captureError } = useGlobalError()

    // Wrap async operations
    const handleAsyncError = (promise: Promise<any>, action?: string) => {
      return promise.catch(error => {
        captureError(
          error instanceof Error ? error : new Error(String(error)),
          componentName,
          action
        )
        throw error // Re-throw to maintain promise rejection
      })
    }

    return (
      <Component 
        {...props} 
        onError={(error: Error, action?: string) => {
          captureError(error, componentName, action)
        }}
        handleAsyncError={handleAsyncError}
      />
    )
  }

  WrappedComponent.displayName = `withGlobalErrorHandler(${componentName || Component.displayName || Component.name})`
  
  return WrappedComponent
}

/**
 * Hook for manual error reporting within components
 */
export function useErrorReporting() {
  const { reportError } = useGlobalError()
  
  const reportAsyncError = async (asyncFn: () => Promise<any>, context?: Record<string, any>) => {
    try {
      return await asyncFn()
    } catch (error) {
      reportError(
        error instanceof Error ? error : new Error(String(error)),
        context
      )
      throw error
    }
  }

  return {
    reportError,
    reportAsyncError
  }
}