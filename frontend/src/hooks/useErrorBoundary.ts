/**
 * Error Boundary Hook for React Error Handling
 * Provides comprehensive error catching and reporting
 */
import { useCallback, useState } from 'react'
import { toast } from 'sonner'

export interface ErrorInfo {
  errorId: string
  timestamp: string
  userAgent: string
  url: string
  userId?: string
  component?: string
  action?: string
  severity: 'low' | 'medium' | 'high' | 'critical'
}

export interface ErrorBoundaryState {
  hasError: boolean
  error: Error | null
  errorInfo: ErrorInfo | null
  retryCount: number
}

export interface UseErrorBoundaryOptions {
  enableLogging?: boolean
  enableToasts?: boolean
  maxRetries?: number
  reportToService?: boolean
}

export function useErrorBoundary(options: UseErrorBoundaryOptions = {}) {
  const {
    enableLogging = true,
    enableToasts = true,
    maxRetries = 3,
    reportToService = true
  } = options

  const [errorState, setErrorState] = useState<ErrorBoundaryState>({
    hasError: false,
    error: null,
    errorInfo: null,
    retryCount: 0
  })

  const generateErrorId = () => {
    return `err_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  }

  const createErrorInfo = (error: Error, component?: string, action?: string): ErrorInfo => {
    return {
      errorId: generateErrorId(),
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      url: window.location.href,
      component,
      action,
      severity: determineSeverity(error)
    }
  }

  const determineSeverity = (error: Error): ErrorInfo['severity'] => {
    const message = error.message.toLowerCase()
    
    if (message.includes('network') || message.includes('fetch')) {
      return 'medium'
    }
    
    if (message.includes('authentication') || message.includes('unauthorized')) {
      return 'high'
    }
    
    if (message.includes('critical') || message.includes('database')) {
      return 'critical'
    }
    
    return 'low'
  }

  const logError = useCallback((error: Error, errorInfo: ErrorInfo) => {
    if (!enableLogging) return

    console.group(`🚨 Error Caught [${errorInfo.severity.toUpperCase()}]`)
    console.error('Error ID:', errorInfo.errorId)
    console.error('Timestamp:', errorInfo.timestamp)
    console.error('Component:', errorInfo.component)
    console.error('Action:', errorInfo.action)
    console.error('Error:', error)
    console.error('Stack:', error.stack)
    console.error('Error Info:', errorInfo)
    console.groupEnd()

    // Store in localStorage for debugging
    try {
      const errorLog = JSON.parse(localStorage.getItem('error_log') || '[]')
      errorLog.push({
        ...errorInfo,
        error: {
          name: error.name,
          message: error.message,
          stack: error.stack
        }
      })
      
      // Keep only last 50 errors
      if (errorLog.length > 50) {
        errorLog.splice(0, errorLog.length - 50)
      }
      
      localStorage.setItem('error_log', JSON.stringify(errorLog))
    } catch (e) {
      console.warn('Failed to store error log:', e)
    }
  }, [enableLogging])

  const reportError = useCallback(async (error: Error, errorInfo: ErrorInfo) => {
    if (!reportToService) return

    try {
      // Report to monitoring service (could be Sentry, LogRocket, etc.)
      await fetch('/api/v1/monitoring/errors', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          errorId: errorInfo.errorId,
          timestamp: errorInfo.timestamp,
          severity: errorInfo.severity,
          component: errorInfo.component,
          action: errorInfo.action,
          error: {
            name: error.name,
            message: error.message,
            stack: error.stack
          },
          context: {
            userAgent: errorInfo.userAgent,
            url: errorInfo.url,
            userId: errorInfo.userId
          }
        })
      })
    } catch (reportingError) {
      console.warn('Failed to report error to service:', reportingError)
    }
  }, [reportToService])

  const showErrorToast = useCallback((error: Error, errorInfo: ErrorInfo) => {
    if (!enableToasts) return

    const getToastMessage = () => {
      switch (errorInfo.severity) {
        case 'critical':
          return {
            title: 'Critical Error',
            description: 'A critical error occurred. Please refresh the page and try again.',
            type: 'error' as const
          }
        case 'high':
          return {
            title: 'Error',
            description: error.message || 'An error occurred. Please try again.',
            type: 'error' as const
          }
        case 'medium':
          return {
            title: 'Warning',
            description: 'Something went wrong. Please check your connection and try again.',
            type: 'warning' as const
          }
        default:
          return {
            title: 'Notice',
            description: 'A minor issue occurred.',
            type: 'info' as const
          }
      }
    }

    const { title, description, type } = getToastMessage()
    
    toast[type](title, {
      description: `${description} (Error ID: ${errorInfo.errorId.slice(-8)})`
    })
  }, [enableToasts])

  const captureError = useCallback((
    error: Error,
    component?: string,
    action?: string,
    userId?: string
  ) => {
    const errorInfo = createErrorInfo(error, component, action)
    if (userId) {
      errorInfo.userId = userId
    }

    logError(error, errorInfo)
    reportError(error, errorInfo)
    showErrorToast(error, errorInfo)

    setErrorState({
      hasError: true,
      error,
      errorInfo,
      retryCount: 0
    })
  }, [logError, reportError, showErrorToast])

  const retry = useCallback(() => {
    if (errorState.retryCount >= maxRetries) {
      toast.error('Maximum retry attempts reached')
      return false
    }

    setErrorState(prev => ({
      ...prev,
      hasError: false,
      retryCount: prev.retryCount + 1
    }))

    return true
  }, [errorState.retryCount, maxRetries])

  const reset = useCallback(() => {
    setErrorState({
      hasError: false,
      error: null,
      errorInfo: null,
      retryCount: 0
    })
  }, [])

  const getErrorLog = useCallback(() => {
    try {
      return JSON.parse(localStorage.getItem('error_log') || '[]')
    } catch (e) {
      return []
    }
  }, [])

  const clearErrorLog = useCallback(() => {
    try {
      localStorage.removeItem('error_log')
    } catch (e) {
      console.warn('Failed to clear error log:', e)
    }
  }, [])

  return {
    errorState,
    captureError,
    retry,
    reset,
    getErrorLog,
    clearErrorLog,
    canRetry: errorState.retryCount < maxRetries,
    hasError: errorState.hasError
  }
}

/**
 * Async Error Handler for Promise-based operations
 */
export function useAsyncErrorHandler(options: UseErrorBoundaryOptions = {}) {
  const { captureError } = useErrorBoundary(options)

  const handleAsync = useCallback(async <T>(
    asyncFn: () => Promise<T>,
    component?: string,
    action?: string
  ): Promise<T | null> => {
    try {
      return await asyncFn()
    } catch (error) {
      captureError(
        error instanceof Error ? error : new Error(String(error)),
        component,
        action
      )
      return null
    }
  }, [captureError])

  return { handleAsync }
}