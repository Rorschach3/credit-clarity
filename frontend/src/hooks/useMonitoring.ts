/**
 * Monitoring and Analytics Hook
 * Tracks user interactions, performance metrics, and system health
 */
import { useCallback, useEffect, useRef, useState } from 'react'
import { useAuth } from './use-auth'
import { supabase } from "@/integrations/supabase/client"

export interface PerformanceMetric {
  name: string
  value: number
  timestamp: string
  tags?: Record<string, string>
}

export interface UserEvent {
  event: string
  properties: Record<string, string | number | boolean | object>;
  timestamp: string
  userId?: string
  sessionId: string
}

export interface SystemHealth {
  websocketConnected: boolean
  apiResponseTime: number
  lastApiCall: string
  errorRate: number
  memoryUsage?: number
}

export interface UseMonitoringOptions {
  enableUserTracking?: boolean;
  enablePerformanceTracking?: boolean;
  enableSystemHealth?: boolean;
  batchSize?: number;
  flushInterval?: number;
}

export function useMonitoring(options: UseMonitoringOptions = {}) {
  const { 
    enableUserTracking = true, 
    enablePerformanceTracking = true,
    enableSystemHealth = true,
    batchSize = 10,
    flushInterval = 30000 // 30 seconds
  } = options;

  const { user } = useAuth()
  const sessionId = useRef(generateSessionId())
  const eventQueue = useRef<UserEvent[]>([])
  const metricsQueue = useRef<PerformanceMetric[]>([])
  const flushTimeoutRef = useRef<NodeJS.Timeout>()
  
  const [systemHealth, setSystemHealth] = useState<SystemHealth>({
    websocketConnected: false,
    apiResponseTime: 0,
    lastApiCall: '',
    errorRate: 0
  })

  function generateSessionId(): string {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  }

  // Performance tracking
  const trackPerformance = useCallback((name: string, value: number, tags?: Record<string, string>) => {
    if (!enablePerformanceTracking) return

    const metric: PerformanceMetric = {
      name,
      value,
      timestamp: new Date().toISOString(),
      tags
    }

    metricsQueue.current.push(metric)

    // Auto-flush if queue is full
    if (metricsQueue.current.length >= batchSize) {
      flushMetrics()
    }
  }, [enablePerformanceTracking, batchSize])

  // User event tracking
  const trackEvent = useCallback((event: string, properties: Record<string, string | number | boolean | object> = {}) => {
    if (!enableUserTracking || typeof window === 'undefined') return

    const userEvent: UserEvent = {
      event,
      properties: {
        ...properties,
        url: window.location.href,
        userAgent: navigator.userAgent,
        timestamp: Date.now()
      },
      timestamp: new Date().toISOString(),
      userId: user?.id,
      sessionId: sessionId.current
    }

    eventQueue.current.push(userEvent)

    // Auto-flush if queue is full
    if (eventQueue.current.length >= batchSize) {
      flushEvents()
    }
  }, [enableUserTracking, user?.id, batchSize])

  // Page view tracking
  const trackPageView = useCallback((page?: string) => {
    if (typeof window === 'undefined') return
    
    trackEvent('page_view', {
      page: page || window.location.pathname,
      referrer: document.referrer,
      title: document.title
    })
  }, [trackEvent])

  // API call tracking
  const trackApiCall = useCallback((
    endpoint: string,
    method: string,
    duration: number,
    status: number,
    error?: string
  ) => {
    trackPerformance('api_call_duration', duration, {
      endpoint,
      method,
      status: status.toString()
    })

    trackEvent('api_call', {
      endpoint,
      method,
      duration,
      status,
      success: status >= 200 && status < 300,
      error: error ? error.toString() : undefined
    })

    // Update system health
    setSystemHealth(prev => ({
      ...prev,
      apiResponseTime: duration,
      lastApiCall: new Date().toISOString(),
      errorRate: status >= 400 ? prev.errorRate + 0.1 : Math.max(0, prev.errorRate - 0.05)
    }))
  }, [trackPerformance, trackEvent])

  // Error tracking
  const trackError = useCallback((
    error: Error,
    context?: Record<string, string | number | boolean | object>
  ) => {
    trackEvent('error', {
      error_name: error.name,
      error_message: error.message,
      error_stack: error.stack || undefined,
      ...context
    })

    // Update error rate
    setSystemHealth(prev => ({
      ...prev,
      errorRate: prev.errorRate + 0.2
    }))
  }, [trackEvent])

  // Timing utilities
  const startTiming = useCallback((name: string) => {
    const startTime = performance.now()
    
    return {
      end: (tags?: Record<string, string>) => {
        const duration = performance.now() - startTime
        trackPerformance(name, duration, tags)
        return duration
      }
    }
  }, [trackPerformance])

  // Measure React component render time
  const measureRender = useCallback((componentName: string) => {
    return startTiming(`component_render_${componentName}`)
  }, [startTiming])

  // Web Vitals tracking
  const trackWebVitals = useCallback(() => {
    if (!enablePerformanceTracking || typeof window === 'undefined') return

    // Largest Contentful Paint
    const observer = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        if (entry.entryType === 'largest-contentful-paint') {
          trackPerformance('lcp', entry.startTime)
        }
      }
    })

    try {
      observer.observe({ type: 'largest-contentful-paint', buffered: true })
    } catch (e) {
      // LCP not supported
    }

    // First Input Delay
    const fidObserver = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        if (entry.entryType === 'first-input') {
          trackPerformance('fid', (entry as any).processingStart - entry.startTime)
        }
      }
    })

    try {
      fidObserver.observe({ type: 'first-input', buffered: true })
    } catch (e) {
      // FID not supported
    }

    // Cumulative Layout Shift
    const clsObserver = new PerformanceObserver((list) => {
      let clsValue = 0
      for (const entry of list.getEntries()) {
        if ((entry as any).hadRecentInput) continue
        clsValue += (entry as any).value
      }
      if (clsValue > 0) {
        trackPerformance('cls', clsValue)
      }
    })

    try {
      clsObserver.observe({ type: 'layout-shift', buffered: true })
    } catch (e) {
      // CLS not supported
    }

    return () => {
      observer.disconnect()
      fidObserver.disconnect()
      clsObserver.disconnect()
    }
  }, [enablePerformanceTracking, trackPerformance])

  // Memory usage tracking
  const trackMemoryUsage = useCallback(() => {
    if (!enableSystemHealth || !(performance as any).memory) return

    const memory = (performance as any).memory
    const usagePercent = (memory.usedJSHeapSize / memory.jsHeapSizeLimit) * 100

    trackPerformance('memory_usage', usagePercent)
    
    setSystemHealth(prev => ({
      ...prev,
      memoryUsage: usagePercent
    }))
  }, [enableSystemHealth, trackPerformance])

  // Flush queued data
  const flushEvents = useCallback(async () => {
    if (eventQueue.current.length === 0) return

    const events = [...eventQueue.current]
    eventQueue.current = []

    try {
      // Get auth headers
      const { data: { session }, error } = await supabase.auth.getSession();
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      };
      
      if (!error && session?.access_token) {
        headers['Authorization'] = `Bearer ${session.access_token}`;
      }
      
      // Use full API URL
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      await fetch(`${apiUrl}/api/v1/monitoring/events`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ events })
      })
    } catch (error) {
      console.warn('Failed to flush events:', error)
      // Put events back in queue
      eventQueue.current.unshift(...events)
    }
  }, [])

  const flushMetrics = useCallback(async () => {
    if (metricsQueue.current.length === 0) return

    const metrics = [...metricsQueue.current]
    metricsQueue.current = []

    try {
      // TODO: Implement monitoring endpoint /api/v1/monitoring/metrics
      console.debug('Metrics collected:', metrics.length, 'items')
      // Use relative URL when backend endpoint is implemented
      // await fetch('/api/v1/monitoring/metrics', {
      //   method: 'POST',
      //   headers: {
      //     'Content-Type': 'application/json',
      //   },
      //   body: JSON.stringify({ metrics })
      // })
    } catch (error) {
      console.warn('Failed to flush metrics:', error)
      // Put metrics back in queue
      metricsQueue.current.unshift(...metrics)
    }
  }, [])

  const flush = useCallback(async () => {
    await Promise.all([flushEvents(), flushMetrics()])
  }, [flushEvents, flushMetrics])

  // Setup auto-flush interval
  useEffect(() => {
    flushTimeoutRef.current = setInterval(() => {
      flush()
    }, flushInterval)

    return () => {
      if (flushTimeoutRef.current) {
        clearInterval(flushTimeoutRef.current)
      }
    }
  }, [flush, flushInterval])

  // Track page views on route changes
  useEffect(() => {
    trackPageView()
  }, [trackPageView]) // Remove window.location.pathname dependency to avoid SSR issues

  // Setup Web Vitals tracking
  useEffect(() => {
    return trackWebVitals()
  }, [trackWebVitals])

  // Track memory usage periodically
  useEffect(() => {
    if (!enableSystemHealth) return

    const interval = setInterval(trackMemoryUsage, 60000) // Every minute
    return () => clearInterval(interval)
  }, [enableSystemHealth, trackMemoryUsage])

  // Cleanup on unmount
  useEffect(() => {
    const handleBeforeUnload = () => {
      // Use sendBeacon for reliable data sending on page unload
      if (navigator.sendBeacon && (eventQueue.current.length > 0 || metricsQueue.current.length > 0)) {
        const data = {
          events: eventQueue.current,
          metrics: metricsQueue.current
        }
        const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
        navigator.sendBeacon(`${apiUrl}/api/v1/monitoring/beacon`, JSON.stringify(data))
      }
    }

    window.addEventListener('beforeunload', handleBeforeUnload)
    
    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload)
      flush() // Final flush
    }
  }, [flush])

  return {
    trackEvent,
    trackPageView,
    trackApiCall,
    trackError,
    trackPerformance,
    startTiming,
    measureRender,
    systemHealth,
    flush,
    sessionId: sessionId.current
  }
}
