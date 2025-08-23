/**
 * Retry Hook with Exponential Backoff
 * Provides retry logic for failed operations with intelligent backoff
 */
import { useState, useCallback, useRef } from 'react'
import { toast } from 'sonner'

export interface RetryOptions {
  maxAttempts?: number
  initialDelay?: number
  maxDelay?: number
  backoffFactor?: number
  retryCondition?: (error: Error) => boolean
  onRetry?: (attempt: number, error: Error) => void
  onSuccess?: (attempt: number, result: any) => void
  onFailure?: (error: Error, attempts: number) => void
}

export interface RetryState {
  isRetrying: boolean
  attempts: number
  lastError: Error | null
  canRetry: boolean
}

export function useRetry(options: RetryOptions = {}) {
  const {
    maxAttempts = 3,
    initialDelay = 1000,
    maxDelay = 10000,
    backoffFactor = 2,
    retryCondition = (error: Error) => {
      // Default retry condition: retry on network errors, server errors, but not auth errors
      const message = error.message.toLowerCase()
      return (
        message.includes('network') ||
        message.includes('timeout') ||
        message.includes('503') ||
        message.includes('502') ||
        message.includes('500')
      ) && !message.includes('401') && !message.includes('403')
    },
    onRetry,
    onSuccess,
    onFailure
  } = options

  const [retryState, setRetryState] = useState<RetryState>({
    isRetrying: false,
    attempts: 0,
    lastError: null,
    canRetry: true
  })

  const timeoutRef = useRef<NodeJS.Timeout>()

  const calculateDelay = useCallback((attempt: number): number => {
    const delay = Math.min(
      initialDelay * Math.pow(backoffFactor, attempt - 1),
      maxDelay
    )
    
    // Add jitter to prevent thundering herd
    const jitter = Math.random() * 0.1 * delay
    return Math.floor(delay + jitter)
  }, [initialDelay, maxDelay, backoffFactor])

  const executeWithRetry = useCallback(async <T>(
    operation: () => Promise<T>,
    customOptions?: Partial<RetryOptions>
  ): Promise<T> => {
    const finalOptions = { ...options, ...customOptions }
    const finalMaxAttempts = finalOptions.maxAttempts || maxAttempts
    const finalRetryCondition = finalOptions.retryCondition || retryCondition

    let attempts = 0
    let lastError: Error

    setRetryState({
      isRetrying: false,
      attempts: 0,
      lastError: null,
      canRetry: true
    })

    const attemptOperation = async (): Promise<T> => {
      attempts++
      
      setRetryState(prev => ({
        ...prev,
        attempts,
        isRetrying: attempts > 1
      }))

      try {
        const result = await operation()
        
        // Success
        setRetryState(prev => ({
          ...prev,
          isRetrying: false,
          canRetry: false
        }))

        if (attempts > 1) {
          onSuccess?.(attempts, result)
          toast.success(`Operation succeeded after ${attempts} attempts`)
        }

        return result
      } catch (error) {
        lastError = error instanceof Error ? error : new Error(String(error))
        
        setRetryState(prev => ({
          ...prev,
          lastError,
          canRetry: attempts < finalMaxAttempts && finalRetryCondition(lastError)
        }))

        // Check if we should retry
        if (attempts < finalMaxAttempts && finalRetryCondition(lastError)) {
          const delay = calculateDelay(attempts)
          
          onRetry?.(attempts, lastError)
          
          console.warn(`Operation failed (attempt ${attempts}/${finalMaxAttempts}). Retrying in ${delay}ms...`, lastError)
          
          // Show retry toast for user feedback
          if (attempts === 1) {
            toast.loading(`Retrying operation... (${attempts}/${finalMaxAttempts})`, {
              id: 'retry-toast'
            })
          } else {
            toast.loading(`Retrying operation... (${attempts}/${finalMaxAttempts})`, {
              id: 'retry-toast'
            })
          }

          return new Promise<T>((resolve, reject) => {
            timeoutRef.current = setTimeout(async () => {
              try {
                const result = await attemptOperation()
                resolve(result)
              } catch (retryError) {
                reject(retryError)
              }
            }, delay)
          })
        } else {
          // Max attempts reached or error not retryable
          setRetryState(prev => ({
            ...prev,
            isRetrying: false,
            canRetry: false
          }))

          onFailure?.(lastError, attempts)
          
          toast.dismiss('retry-toast')
          
          if (attempts >= finalMaxAttempts) {
            toast.error(`Operation failed after ${attempts} attempts`)
          } else {
            toast.error('Operation failed (not retryable)')
          }

          throw lastError
        }
      }
    }

    return attemptOperation()
  }, [calculateDelay, maxAttempts, retryCondition, onRetry, onSuccess, onFailure])

  const reset = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
    }
    
    setRetryState({
      isRetrying: false,
      attempts: 0,
      lastError: null,
      canRetry: true
    })
    
    toast.dismiss('retry-toast')
  }, [])

  const cancel = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
    }
    
    setRetryState(prev => ({
      ...prev,
      isRetrying: false,
      canRetry: false
    }))
    
    toast.dismiss('retry-toast')
  }, [])

  return {
    executeWithRetry,
    retryState,
    reset,
    cancel
  }
}

/**
 * Specialized retry hook for API calls
 */
export function useApiRetry(options: RetryOptions = {}) {
  const apiRetryCondition = useCallback((error: Error) => {
    const message = error.message.toLowerCase()
    const status = extractStatusCode(error.message)
    
    // Retry on network errors and server errors, but not client errors
    return (
      message.includes('network') ||
      message.includes('timeout') ||
      message.includes('fetch') ||
      (status && status >= 500) ||
      status === 429 // Rate limited
    ) && status !== 401 && status !== 403 && status !== 404
  }, [])

  return useRetry({
    maxAttempts: 3,
    initialDelay: 1000,
    retryCondition: apiRetryCondition,
    ...options
  })
}

/**
 * Specialized retry hook for file uploads
 */
export function useUploadRetry(options: RetryOptions = {}) {
  const uploadRetryCondition = useCallback((error: Error) => {
    const message = error.message.toLowerCase()
    
    // Retry on network issues but not on validation errors
    return (
      message.includes('network') ||
      message.includes('timeout') ||
      message.includes('connection') ||
      message.includes('503') ||
      message.includes('502')
    ) && !message.includes('invalid') && !message.includes('too large')
  }, [])

  return useRetry({
    maxAttempts: 2, // Fewer retries for uploads
    initialDelay: 2000, // Longer initial delay
    retryCondition: uploadRetryCondition,
    ...options
  })
}

// Helper function to extract status code from error message
function extractStatusCode(message: string): number | null {
  const match = message.match(/\b(\d{3})\b/)
  return match ? parseInt(match[1], 10) : null
}