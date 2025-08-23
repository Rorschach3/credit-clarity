/**
 * Real-time Progress Indicator with WebSocket updates
 * Shows live progress, stage information, and estimated completion time
 */
import React from 'react';
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Loader2, Clock, FileText, CheckCircle, AlertCircle, WifiOff } from "lucide-react";
import { useRealtime, useJobProgress } from "@/hooks/useRealtime";

interface RealtimeProgressIndicatorProps {
  jobId?: string;
  progress: number;
  message?: string;
  estimatedTimeMs?: number | null;
  tradelinesFound?: number;
  stage?: string;
  isProcessing: boolean;
  className?: string;
}

interface ProgressStage {
  name: string;
  description: string;
  icon: React.ReactNode;
  color: string;
  minProgress: number;
}

const PROCESSING_STAGES: ProgressStage[] = [
  {
    name: 'initialization',
    description: 'Preparing for processing',
    icon: <Loader2 className="h-4 w-4 animate-spin" />,
    color: 'bg-blue-500',
    minProgress: 0,
  },
  {
    name: 'extraction',
    description: 'Extracting text and data',
    icon: <FileText className="h-4 w-4" />,
    color: 'bg-yellow-500',
    minProgress: 20,
  },
  {
    name: 'processing',
    description: 'Analyzing credit data',
    icon: <Loader2 className="h-4 w-4 animate-spin" />,
    color: 'bg-orange-500',
    minProgress: 40,
  },
  {
    name: 'saving',
    description: 'Saving to database',
    icon: <Loader2 className="h-4 w-4 animate-spin" />,
    color: 'bg-purple-500',
    minProgress: 80,
  },
  {
    name: 'completed',
    description: 'Processing complete',
    icon: <CheckCircle className="h-4 w-4" />,
    color: 'bg-green-500',
    minProgress: 100,
  },
  {
    name: 'warning',
    description: 'Completed with warnings',
    icon: <AlertCircle className="h-4 w-4" />,
    color: 'bg-yellow-500',
    minProgress: 100,
  },
];

function formatTimeEstimate(timeMs: number): string {
  const totalSeconds = Math.ceil(timeMs / 1000);
  
  if (totalSeconds < 60) {
    return `${totalSeconds}s`;
  } else if (totalSeconds < 3600) {
    const minutes = Math.ceil(totalSeconds / 60);
    return `${minutes}m`;
  } else {
    const hours = Math.floor(totalSeconds / 3600);
    const minutes = Math.ceil((totalSeconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  }
}

function getCurrentStage(stageName?: string, progress?: number): ProgressStage {
  // Try to find by stage name first
  if (stageName) {
    const foundStage = PROCESSING_STAGES.find(stage => stage.name === stageName);
    if (foundStage) return foundStage;
  }
  
  // Fallback to progress-based stage detection
  const progressValue = progress || 0;
  for (let i = PROCESSING_STAGES.length - 1; i >= 0; i--) {
    if (progressValue >= PROCESSING_STAGES[i].minProgress) {
      return PROCESSING_STAGES[i];
    }
  }
  
  return PROCESSING_STAGES[0];
}

export function RealtimeProgressIndicator({
  jobId,
  progress,
  message,
  estimatedTimeMs,
  tradelinesFound,
  stage,
  isProcessing,
  className,
}: RealtimeProgressIndicatorProps) {
  const { isConnected, connectionError } = useRealtime();
  const realtimeProgress = useJobProgress(jobId);
  
  // Use real-time data if available, otherwise fall back to props
  const currentProgress = realtimeProgress?.progress ?? progress;
  const currentMessage = realtimeProgress?.message ?? message ?? '';
  const currentStage = realtimeProgress?.stage ?? stage;
  const currentETA = realtimeProgress?.estimated_time_remaining ?? estimatedTimeMs;
  const currentTradelinesFound = realtimeProgress?.tradelines_found ?? tradelinesFound;
  
  const stageInfo = getCurrentStage(currentStage, currentProgress);
  
  if (!isProcessing && currentProgress === 0) {
    return null;
  }

  return (
    <Card className={`w-full ${className}`}>
      <CardContent className="p-6 space-y-4">
        {/* Header with connection status */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <stageInfo.icon />
            <h3 className="text-lg font-semibold">Processing Credit Report</h3>
          </div>
          
          <div className="flex items-center space-x-2">
            {!isConnected && (
              <Badge variant="outline" className="text-orange-600">
                <WifiOff className="h-3 w-3 mr-1" />
                Offline Mode
              </Badge>
            )}
            
            {isConnected && (
              <Badge variant="outline" className="text-green-600">
                <div className="h-2 w-2 bg-green-500 rounded-full mr-1 animate-pulse" />
                Live Updates
              </Badge>
            )}
          </div>
        </div>

        {/* Progress Bar */}
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span className="font-medium">{stageInfo.description}</span>
            <span className="text-muted-foreground">{Math.round(currentProgress)}%</span>
          </div>
          
          <Progress 
            value={currentProgress} 
            className="h-3"
          />
        </div>

        {/* Current Status Message */}
        {currentMessage && (
          <div className="bg-muted/50 p-3 rounded-lg">
            <p className="text-sm text-muted-foreground">{currentMessage}</p>
          </div>
        )}

        {/* Stage Indicators */}
        <div className="flex justify-between items-center">
          {PROCESSING_STAGES.filter(s => !['warning'].includes(s.name)).map((stage, index) => {
            const isActive = currentProgress >= stage.minProgress;
            const isCurrent = stageInfo.name === stage.name;
            
            return (
              <div key={stage.name} className="flex flex-col items-center space-y-1">
                <div
                  className={`
                    w-8 h-8 rounded-full flex items-center justify-center transition-colors
                    ${isActive 
                      ? isCurrent 
                        ? `${stage.color} text-white shadow-md` 
                        : 'bg-green-500 text-white'
                      : 'bg-muted text-muted-foreground'
                    }
                  `}
                >
                  {isActive && stage.name !== stageInfo.name ? (
                    <CheckCircle className="h-4 w-4" />
                  ) : (
                    stage.icon
                  )}
                </div>
                
                <span className={`text-xs ${isActive ? 'text-foreground' : 'text-muted-foreground'}`}>
                  {stage.description.split(' ')[0]}
                </span>
              </div>
            );
          })}
        </div>

        {/* Additional Info */}
        <div className="flex justify-between items-center text-sm text-muted-foreground">
          <div className="flex items-center space-x-4">
            {currentETA && currentETA > 0 && (
              <div className="flex items-center space-x-1">
                <Clock className="h-4 w-4" />
                <span>~{formatTimeEstimate(currentETA)} remaining</span>
              </div>
            )}
            
            {currentTradelinesFound !== undefined && currentTradelinesFound > 0 && (
              <div className="flex items-center space-x-1">
                <FileText className="h-4 w-4" />
                <span>{currentTradelinesFound} tradelines found</span>
              </div>
            )}
          </div>
          
          {jobId && (
            <div className="text-xs">
              Job ID: {jobId.slice(-8)}
            </div>
          )}
        </div>

        {/* Connection Error Warning */}
        {connectionError && (
          <div className="bg-red-50 border border-red-200 p-3 rounded-lg">
            <div className="flex items-center space-x-2 text-red-800">
              <AlertCircle className="h-4 w-4" />
              <span className="text-sm font-medium">Connection Issue</span>
            </div>
            <p className="text-sm text-red-600 mt-1">
              {connectionError}. Progress updates may be delayed.
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// Simpler version for compact spaces
export function CompactRealtimeProgress({
  jobId,
  progress,
  message,
  isProcessing,
}: Pick<RealtimeProgressIndicatorProps, 'jobId' | 'progress' | 'message' | 'isProcessing'>) {
  const { isConnected } = useRealtime();
  const realtimeProgress = useJobProgress(jobId);
  
  const currentProgress = realtimeProgress?.progress ?? progress;
  const currentMessage = realtimeProgress?.message ?? message ?? 'Processing...';
  
  if (!isProcessing && currentProgress === 0) {
    return null;
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-sm">
        <div className="flex items-center space-x-2">
          <Loader2 className="h-4 w-4 animate-spin" />
          <span>{currentMessage}</span>
        </div>
        
        <div className="flex items-center space-x-2">
          <span className="text-muted-foreground">{Math.round(currentProgress)}%</span>
          {isConnected && (
            <div className="h-2 w-2 bg-green-500 rounded-full animate-pulse" />
          )}
        </div>
      </div>
      
      <Progress value={currentProgress} className="h-2" />
    </div>
  );
}