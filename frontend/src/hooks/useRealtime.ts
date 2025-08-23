/**
 * Real-time WebSocket hook for Credit Clarity
 * Provides real-time updates for job progress, credit scores, and notifications
 */
import { useEffect, useRef, useState, useCallback } from 'react'
import { useAuth } from './use-auth'
import { toast } from 'sonner'

export interface RealtimeEvent {
  event_type: string
  user_id: string
  data: any
  timestamp: string
  event_id: string
}

export interface JobProgressData {
  job_id: string
  progress: number
  message: string
  estimated_time_remaining?: number
  stage?: string
  tradelines_found?: number
}

export interface CreditScoreUpdate {
  old_score: number
  new_score: number
  change: number
  bureau: string
  factors: string[]
}

export interface UseRealtimeOptions {
  autoConnect?: boolean
  enableToasts?: boolean
  reconnectAttempts?: number
  reconnectDelay?: number
  heartbeatInterval?: number
}

export interface UseRealtimeReturn {
  isConnected: boolean
  isConnecting: boolean
  connectionError: string | null
  connect: () => void
  disconnect: () => void
  sendMessage: (message: any) => void
  lastEvent: RealtimeEvent | null
  connectionCount: number
}

export function useRealtime(options: UseRealtimeOptions = {}): UseRealtimeReturn {
  const {
    autoConnect = true,
    enableToasts = true,
    reconnectAttempts = 5,
    reconnectDelay = 3000,
    heartbeatInterval = 30000
  } = options

  const { user, getToken } = useAuth()
  
  const [isConnected, setIsConnected] = useState(false)
  const [isConnecting, setIsConnecting] = useState(false)
  const [connectionError, setConnectionError] = useState<string | null>(null)
  const [lastEvent, setLastEvent] = useState<RealtimeEvent | null>(null)
  const [connectionCount, setConnectionCount] = useState(0)
  
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const heartbeatIntervalRef = useRef<NodeJS.Interval | null>(null)
  const reconnectAttemptsRef = useRef(0)

  const getWebSocketUrl = useCallback(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = process.env.NODE_ENV === 'production' 
      ? window.location.host 
      : 'localhost:8000'
    
    return `${protocol}//${host}/api/v1/ws/connect`
  }, [])

  const connect = useCallback(async () => {
    if (isConnecting || isConnected || !user) {
      return
    }

    try {
      setIsConnecting(true)
      setConnectionError(null)

      const token = await getToken()
      if (!token) {
        throw new Error('No authentication token available')
      }

      const wsUrl = `${getWebSocketUrl()}?token=${encodeURIComponent(token)}&client_type=web&app_version=${process.env.REACT_APP_VERSION || '1.0.0'}`
      
      const ws = new WebSocket(wsUrl)
      wsRef.current = ws

      ws.onopen = () => {
        setIsConnected(true)
        setIsConnecting(false)
        setConnectionError(null)
        reconnectAttemptsRef.current = 0
        
        if (enableToasts) {
          toast.success('Real-time connection established')
        }

        // Start heartbeat
        if (heartbeatIntervalRef.current) {
          clearInterval(heartbeatIntervalRef.current)
        }
        
        heartbeatIntervalRef.current = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'heartbeat', timestamp: Date.now() }))
          }
        }, heartbeatInterval)
      }

      ws.onmessage = (event) => {
        try {
          const realtimeEvent: RealtimeEvent = JSON.parse(event.data)
          setLastEvent(realtimeEvent)
          
          // Handle different event types
          handleRealtimeEvent(realtimeEvent)
          
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error)
        }
      }

      ws.onclose = (event) => {
        setIsConnected(false)
        setIsConnecting(false)
        
        if (heartbeatIntervalRef.current) {
          clearInterval(heartbeatIntervalRef.current)
          heartbeatIntervalRef.current = null
        }

        // Only attempt reconnection if it wasn't a normal closure
        if (event.code !== 1000 && reconnectAttemptsRef.current < reconnectAttempts) {
          reconnectAttemptsRef.current++
          
          if (enableToasts) {
            toast.warning(`Connection lost. Reconnecting... (${reconnectAttemptsRef.current}/${reconnectAttempts})`)
          }

          reconnectTimeoutRef.current = setTimeout(() => {
            connect()
          }, reconnectDelay * reconnectAttemptsRef.current)
        } else if (reconnectAttemptsRef.current >= reconnectAttempts) {
          setConnectionError('Failed to reconnect after multiple attempts')
          
          if (enableToasts) {
            toast.error('Real-time connection failed. Please refresh the page.')
          }
        }
      }

      ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        setConnectionError('Connection error occurred')
        setIsConnecting(false)
      }

    } catch (error) {
      console.error('Failed to connect WebSocket:', error)
      setConnectionError(error instanceof Error ? error.message : 'Unknown connection error')
      setIsConnecting(false)
    }
  }, [user, getToken, isConnecting, isConnected, getWebSocketUrl, enableToasts, reconnectAttempts, reconnectDelay, heartbeatInterval])

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }

    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current)
      heartbeatIntervalRef.current = null
    }

    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.close(1000, 'Client disconnect')
    }

    wsRef.current = null
    setIsConnected(false)
    setIsConnecting(false)
    setConnectionError(null)
    reconnectAttemptsRef.current = 0
  }, [])

  const sendMessage = useCallback((message: any) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message))
    } else {
      console.warn('WebSocket is not connected')
    }
  }, [])

  const handleRealtimeEvent = useCallback((event: RealtimeEvent) => {
    switch (event.event_type) {
      case 'job:progress':
        // Job progress events will be handled by specific hooks
        break
        
      case 'job:completed':
        if (enableToasts) {
          toast.success('Processing completed!', {
            description: `Job ${event.data.job_id} finished successfully`
          })
        }
        break
        
      case 'job:failed':
        if (enableToasts) {
          toast.error('Processing failed', {
            description: event.data.error || 'Unknown error occurred'
          })
        }
        break
        
      case 'credit:score_updated':
        const scoreData = event.data as CreditScoreUpdate
        if (enableToasts) {
          const changeText = scoreData.change > 0 ? 'increased' : 'decreased'
          toast.info(`Credit score ${changeText}!`, {
            description: `${scoreData.bureau} score: ${scoreData.old_score} → ${scoreData.new_score}`
          })
        }
        break
        
      case 'tradelines:updated':
        if (enableToasts) {
          toast.info('Tradelines updated', {
            description: 'Your credit report data has been updated'
          })
        }
        break
        
      case 'notification':
        if (enableToasts && event.data.message) {
          const toastType = event.data.type === 'error' ? 'error' : 
                           event.data.type === 'warning' ? 'warning' : 'info'
          
          toast[toastType](event.data.message)
        }
        break
        
      case 'system:status':
        if (event.data.type === 'heartbeat_ack') {
          // Handle heartbeat acknowledgment
          setConnectionCount(prev => prev + 1)
        }
        break
        
      default:
        console.log('Unhandled realtime event:', event)
    }
  }, [enableToasts])

  // Auto-connect effect
  useEffect(() => {
    if (autoConnect && user && !isConnected && !isConnecting) {
      connect()
    }
  }, [autoConnect, user, isConnected, isConnecting, connect])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnect()
    }
  }, [disconnect])

  // Handle auth state changes
  useEffect(() => {
    if (!user && isConnected) {
      disconnect()
    }
  }, [user, isConnected, disconnect])

  return {
    isConnected,
    isConnecting,
    connectionError,
    connect,
    disconnect,
    sendMessage,
    lastEvent,
    connectionCount
  }
}

/**
 * Hook specifically for job progress tracking
 */
export function useJobProgress(jobId?: string) {
  const { lastEvent } = useRealtime()
  const [jobProgress, setJobProgress] = useState<JobProgressData | null>(null)

  useEffect(() => {
    if (
      lastEvent?.event_type === 'job:progress' && 
      (!jobId || lastEvent.data.job_id === jobId)
    ) {
      setJobProgress(lastEvent.data as JobProgressData)
    }
  }, [lastEvent, jobId])

  return jobProgress
}

/**
 * Hook for credit score updates
 */
export function useCreditScoreUpdates() {
  const { lastEvent } = useRealtime()
  const [scoreUpdate, setScoreUpdate] = useState<CreditScoreUpdate | null>(null)

  useEffect(() => {
    if (lastEvent?.event_type === 'credit:score_updated') {
      setScoreUpdate(lastEvent.data as CreditScoreUpdate)
    }
  }, [lastEvent])

  return scoreUpdate
}