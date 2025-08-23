/**
 * React Error Boundary Component
 * Catches and handles React component errors gracefully
 */
import React, { Component, ReactNode } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { RefreshCw, Bug, AlertTriangle, Home, Copy } from 'lucide-react'
import { toast } from 'sonner'

interface ErrorInfo {
  componentStack: string
  errorBoundary?: string
  errorBoundaryStack?: string
}

interface ErrorBoundaryState {
  hasError: boolean
  error: Error | null
  errorInfo: ErrorInfo | null
  errorId: string
  retryCount: number
}

interface ErrorBoundaryProps {
  children: ReactNode
  fallback?: React.ComponentType<{
    error: Error
    retry: () => void
    reset: () => void
  }>
  enableReporting?: boolean
  maxRetries?: number
  onError?: (error: Error, errorInfo: ErrorInfo) => void
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  private retryTimeouts: NodeJS.Timeout[] = []

  constructor(props: ErrorBoundaryProps) {
    super(props)
    
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: '',
      retryCount: 0
    }
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    const errorId = `err_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    
    return {
      hasError: true,
      error,
      errorId
    }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    this.setState({ errorInfo })

    // Log error
    console.group(`🚨 React Error Boundary Caught Error`)
    console.error('Error ID:', this.state.errorId)
    console.error('Error:', error)
    console.error('Component Stack:', errorInfo.componentStack)
    console.error('Error Boundary Stack:', errorInfo.errorBoundaryStack)
    console.groupEnd()

    // Report error
    this.reportError(error, errorInfo)

    // Call custom error handler
    this.props.onError?.(error, errorInfo)

    // Store error for debugging
    this.storeErrorLog(error, errorInfo)
  }

  componentWillUnmount() {
    // Clear any pending retry timeouts
    this.retryTimeouts.forEach(timeout => clearTimeout(timeout))
  }

  private reportError = async (error: Error, errorInfo: ErrorInfo) => {
    if (!this.props.enableReporting) return

    try {
      await fetch('/api/v1/monitoring/react-errors', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          errorId: this.state.errorId,
          timestamp: new Date().toISOString(),
          error: {
            name: error.name,
            message: error.message,
            stack: error.stack
          },
          errorInfo,
          context: {
            userAgent: navigator.userAgent,
            url: window.location.href,
            retryCount: this.state.retryCount
          }
        })
      })
    } catch (reportingError) {
      console.warn('Failed to report React error:', reportingError)
    }
  }

  private storeErrorLog = (error: Error, errorInfo: ErrorInfo) => {
    try {
      const errorLog = JSON.parse(localStorage.getItem('react_error_log') || '[]')
      errorLog.push({
        errorId: this.state.errorId,
        timestamp: new Date().toISOString(),
        error: {
          name: error.name,
          message: error.message,
          stack: error.stack
        },
        errorInfo,
        retryCount: this.state.retryCount
      })
      
      // Keep only last 20 React errors
      if (errorLog.length > 20) {
        errorLog.splice(0, errorLog.length - 20)
      }
      
      localStorage.setItem('react_error_log', JSON.stringify(errorLog))
    } catch (e) {
      console.warn('Failed to store React error log:', e)
    }
  }

  private retry = () => {
    const maxRetries = this.props.maxRetries || 3
    
    if (this.state.retryCount >= maxRetries) {
      toast.error('Maximum retry attempts reached')
      return
    }

    this.setState(prevState => ({
      hasError: false,
      error: null,
      errorInfo: null,
      retryCount: prevState.retryCount + 1
    }))

    toast.info(`Retrying... (${this.state.retryCount + 1}/${maxRetries})`)
  }

  private reset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: '',
      retryCount: 0
    })
  }

  private copyErrorInfo = () => {
    const errorText = `
Error ID: ${this.state.errorId}
Error: ${this.state.error?.message}
Stack: ${this.state.error?.stack}
Component Stack: ${this.state.errorInfo?.componentStack}
URL: ${window.location.href}
User Agent: ${navigator.userAgent}
Timestamp: ${new Date().toISOString()}
    `.trim()

    navigator.clipboard.writeText(errorText).then(() => {
      toast.success('Error information copied to clipboard')
    }).catch(() => {
      toast.error('Failed to copy error information')
    })
  }

  private goHome = () => {
    window.location.href = '/'
  }

  render() {
    if (this.state.hasError) {
      const { fallback: FallbackComponent } = this.props
      
      if (FallbackComponent) {
        return (
          <FallbackComponent
            error={this.state.error!}
            retry={this.retry}
            reset={this.reset}
          />
        )
      }

      return (
        <div className="min-h-screen flex items-center justify-center p-4 bg-gray-50">
          <Card className="w-full max-w-2xl">
            <CardHeader className="text-center">
              <div className="mx-auto w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mb-4">
                <AlertTriangle className="w-8 h-8 text-red-600" />
              </div>
              <CardTitle className="text-2xl text-red-600">
                Something went wrong
              </CardTitle>
            </CardHeader>
            
            <CardContent className="space-y-6">
              <Alert>
                <Bug className="h-4 w-4" />
                <AlertDescription>
                  An unexpected error occurred in the application. We've been notified and are working to fix it.
                </AlertDescription>
              </Alert>

              <div className="bg-gray-100 p-4 rounded-lg">
                <h4 className="font-semibold mb-2">Error Details:</h4>
                <p className="text-sm text-gray-600 mb-2">
                  <strong>Error ID:</strong> {this.state.errorId}
                </p>
                <p className="text-sm text-gray-600 mb-2">
                  <strong>Message:</strong> {this.state.error?.message}
                </p>
                {process.env.NODE_ENV === 'development' && (
                  <details className="mt-4">
                    <summary className="cursor-pointer text-sm font-medium">
                      Technical Details (Development)
                    </summary>
                    <pre className="mt-2 text-xs bg-gray-200 p-2 rounded overflow-auto max-h-40">
                      {this.state.error?.stack}
                    </pre>
                    <pre className="mt-2 text-xs bg-gray-200 p-2 rounded overflow-auto max-h-40">
                      Component Stack: {this.state.errorInfo?.componentStack}
                    </pre>
                  </details>
                )}
              </div>

              <div className="flex flex-col sm:flex-row gap-3">
                <Button 
                  onClick={this.retry}
                  disabled={this.state.retryCount >= (this.props.maxRetries || 3)}
                  className="flex-1"
                >
                  <RefreshCw className="w-4 h-4 mr-2" />
                  Try Again ({this.state.retryCount}/{this.props.maxRetries || 3})
                </Button>
                
                <Button variant="outline" onClick={this.goHome} className="flex-1">
                  <Home className="w-4 h-4 mr-2" />
                  Go Home
                </Button>
                
                <Button variant="outline" onClick={this.copyErrorInfo}>
                  <Copy className="w-4 h-4 mr-2" />
                  Copy Error
                </Button>
              </div>

              <div className="text-center text-sm text-gray-500">
                If this problem persists, please contact support with Error ID: 
                <code className="bg-gray-200 px-1 rounded ml-1">
                  {this.state.errorId.slice(-8)}
                </code>
              </div>
            </CardContent>
          </Card>
        </div>
      )
    }

    return this.props.children
  }
}

/**
 * Higher-order component for wrapping components with error boundaries
 */
export function withErrorBoundary<P extends object>(
  Component: React.ComponentType<P>,
  errorBoundaryProps?: Omit<ErrorBoundaryProps, 'children'>
) {
  const WrappedComponent = (props: P) => (
    <ErrorBoundary {...errorBoundaryProps}>
      <Component {...props} />
    </ErrorBoundary>
  )

  WrappedComponent.displayName = `withErrorBoundary(${Component.displayName || Component.name})`
  
  return WrappedComponent
}