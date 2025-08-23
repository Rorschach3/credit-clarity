/**
 * System Health Indicator Component
 * Shows real-time system status and health metrics
 */
import React from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { 
  Wifi, 
  WifiOff, 
  Activity, 
  AlertTriangle, 
  CheckCircle, 
  Clock,
  Database,
  Zap
} from 'lucide-react'
import { useMonitoring } from '@/hooks/useMonitoring'
import { useRealtime } from '@/hooks/useRealtime'

interface SystemHealthIndicatorProps {
  showDetails?: boolean
  className?: string
}

export function SystemHealthIndicator({ 
  showDetails = false, 
  className = '' 
}: SystemHealthIndicatorProps) {
  const { systemHealth } = useMonitoring()
  const { isConnected, connectionError } = useRealtime()

  const getHealthStatus = () => {
    if (connectionError || systemHealth.errorRate > 0.5) {
      return { status: 'critical', color: 'red', icon: AlertTriangle }
    }
    
    if (!isConnected || systemHealth.errorRate > 0.2 || systemHealth.apiResponseTime > 2000) {
      return { status: 'warning', color: 'yellow', icon: AlertTriangle }
    }
    
    return { status: 'healthy', color: 'green', icon: CheckCircle }
  }

  const health = getHealthStatus()
  const StatusIcon = health.icon

  const formatResponseTime = (ms: number) => {
    if (ms > 1000) {
      return `${(ms / 1000).toFixed(1)}s`
    }
    return `${Math.round(ms)}ms`
  }

  const getErrorRateColor = (rate: number) => {
    if (rate > 0.5) return 'text-red-600'
    if (rate > 0.2) return 'text-yellow-600'
    return 'text-green-600'
  }

  if (!showDetails) {
    // Compact indicator
    return (
      <div className={`flex items-center space-x-2 ${className}`}>
        <div className="flex items-center space-x-1">
          {isConnected ? (
            <Wifi className="h-4 w-4 text-green-600" />
          ) : (
            <WifiOff className="h-4 w-4 text-red-600" />
          )}
          <StatusIcon className={`h-4 w-4 text-${health.color}-600`} />
        </div>
        
        <Badge 
          variant={health.status === 'healthy' ? 'default' : 'destructive'}
          className="text-xs"
        >
          {health.status}
        </Badge>
      </div>
    )
  }

  return (
    <Card className={className}>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center justify-between text-lg">
          <div className="flex items-center space-x-2">
            <Activity className="h-5 w-5" />
            <span>System Health</span>
          </div>
          
          <Badge 
            variant={health.status === 'healthy' ? 'default' : 'destructive'}
            className="capitalize"
          >
            <StatusIcon className="h-3 w-3 mr-1" />
            {health.status}
          </Badge>
        </CardTitle>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {/* Connection Status */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            {isConnected ? (
              <Wifi className="h-4 w-4 text-green-600" />
            ) : (
              <WifiOff className="h-4 w-4 text-red-600" />
            )}
            <span className="text-sm font-medium">WebSocket</span>
          </div>
          
          <Badge variant={isConnected ? 'default' : 'destructive'}>
            {isConnected ? 'Connected' : 'Disconnected'}
          </Badge>
        </div>

        {connectionError && (
          <div className="text-sm text-red-600 bg-red-50 p-2 rounded">
            {connectionError}
          </div>
        )}

        {/* API Response Time */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Clock className="h-4 w-4 text-blue-600" />
              <span className="text-sm font-medium">API Response</span>
            </div>
            
            <span className="text-sm text-muted-foreground">
              {systemHealth.apiResponseTime > 0 ? formatResponseTime(systemHealth.apiResponseTime) : 'N/A'}
            </span>
          </div>
          
          {systemHealth.apiResponseTime > 0 && (
            <Progress 
              value={Math.min((systemHealth.apiResponseTime / 3000) * 100, 100)} 
              className="h-2"
            />
          )}
        </div>

        {/* Error Rate */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <AlertTriangle className="h-4 w-4 text-orange-600" />
              <span className="text-sm font-medium">Error Rate</span>
            </div>
            
            <span className={`text-sm font-medium ${getErrorRateColor(systemHealth.errorRate)}`}>
              {(systemHealth.errorRate * 100).toFixed(1)}%
            </span>
          </div>
          
          <Progress 
            value={Math.min(systemHealth.errorRate * 100, 100)} 
            className="h-2"
          />
        </div>

        {/* Memory Usage */}
        {systemHealth.memoryUsage !== undefined && (
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Database className="h-4 w-4 text-purple-600" />
                <span className="text-sm font-medium">Memory Usage</span>
              </div>
              
              <span className="text-sm text-muted-foreground">
                {systemHealth.memoryUsage.toFixed(1)}%
              </span>
            </div>
            
            <Progress 
              value={systemHealth.memoryUsage} 
              className="h-2"
            />
          </div>
        )}

        {/* Last API Call */}
        {systemHealth.lastApiCall && (
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>Last API call:</span>
            <span>{new Date(systemHealth.lastApiCall).toLocaleTimeString()}</span>
          </div>
        )}

        {/* Performance Tips */}
        {(systemHealth.errorRate > 0.2 || systemHealth.apiResponseTime > 2000) && (
          <div className="bg-yellow-50 p-3 rounded-lg border border-yellow-200">
            <div className="flex items-start space-x-2">
              <Zap className="h-4 w-4 text-yellow-600 mt-0.5 flex-shrink-0" />
              <div className="text-sm">
                <p className="font-medium text-yellow-800">Performance Notice</p>
                <p className="text-yellow-700 mt-1">
                  {systemHealth.apiResponseTime > 2000 && 'API responses are slower than usual. '}
                  {systemHealth.errorRate > 0.2 && 'Increased error rate detected. '}
                  Consider refreshing the page if issues persist.
                </p>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

/**
 * Compact system health badge for navigation
 */
export function SystemHealthBadge({ className = '' }: { className?: string }) {
  return (
    <SystemHealthIndicator 
      showDetails={false} 
      className={className}
    />
  )
}