import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Loader2, FileText, Brain, Eye, CheckCircle, XCircle, Clock } from 'lucide-react';
import { ProcessingProgress as ProcessingProgressType } from '@/utils/asyncProcessing';

interface ProcessingProgressProps {
  isProcessing: boolean;
  progress: ProcessingProgressType;
  processingMethod: 'ocr' | 'ai';
}

export const ProcessingProgress: React.FC<ProcessingProgressProps> = ({
  isProcessing,
  progress,
  processingMethod
}) => {
  // Show component if processing OR if there's a step/message to display
  const shouldShow = isProcessing || progress.step || progress.message;
  
  if (!shouldShow) {
    return null;
  }
  
  // Determine completion status
  const isCompleted = progress.step === 'Complete!' || progress.progress === 100;
  const isFailed = progress.step === 'Failed' || progress.step.includes('❌');
  const isInProgress = isProcessing && !isCompleted && !isFailed;

  const getIcon = () => {
    // Show completion status icons first
    if (isCompleted) {
      return <CheckCircle className="h-5 w-5 text-green-600" />;
    }
    if (isFailed) {
      return <XCircle className="h-5 w-5 text-red-600" />;
    }
    
    // Show processing method icons
    switch (processingMethod) {
      case 'ocr':
        return <Eye className="h-5 w-5" />;
      case 'ai':
        return <Brain className="h-5 w-5" />;
      default:
        return <FileText className="h-5 w-5" />;
    }
  };

  const getMethodLabel = () => {
    // Show completion status labels first
    if (isCompleted) {
      return '🎉 Processing Complete!';
    }
    if (isFailed) {
      return '❌ Processing Failed';
    }
    
    // Show processing method labels
    switch (processingMethod) {
      case 'ocr':
        return 'OCR Processing';
      case 'ai':
        return 'AI Analysis';
      default:
        return 'Processing';
    }
  };

  // Dynamic styling based on status
  const getCardStyle = () => {
    if (isCompleted) {
      return "border-green-200 bg-green-50 dark:bg-green-900/20";
    }
    if (isFailed) {
      return "border-red-200 bg-red-50 dark:bg-red-900/20";
    }
    return "border-blue-200 bg-blue-50 dark:bg-blue-900/20";
  };
  
  const getBadgeStyle = () => {
    if (isCompleted) {
      return "bg-green-100 text-green-800";
    }
    if (isFailed) {
      return "bg-red-100 text-red-800";
    }
    return "";
  };

  return (
    <Card className={getCardStyle()}>
      <CardHeader className="pb-3">
        <CardTitle className="text-lg flex items-center gap-2">
          {getIcon()}
          {getMethodLabel()}
          <Badge variant="secondary" className={`ml-auto ${getBadgeStyle()}`}>
            {isCompleted ? '✓' : isFailed ? '✗' : `${progress.progress}%`}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">{progress.step}</span>
            {isInProgress && <Loader2 className="h-4 w-4 animate-spin" />}
            {isCompleted && <Clock className="h-4 w-4 text-green-600" />}
            {isFailed && <XCircle className="h-4 w-4 text-red-600" />}
          </div>
          <Progress 
            value={progress.progress} 
            className={`w-full ${isCompleted ? 'bg-green-200' : isFailed ? 'bg-red-200' : ''}`} 
          />
          <p className="text-sm text-muted-foreground">{progress.message}</p>
        </div>
        
        {/* Processing stages indicator */}
        <div className="grid grid-cols-4 gap-2 mt-4">
          <div className={`text-center p-2 rounded text-xs ${
            progress.progress >= 25 ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-600'
          }`}>
            {progress.progress >= 25 ? '✓' : ''} Initialize
          </div>
          <div className={`text-center p-2 rounded text-xs ${
            progress.progress >= 50 ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-600'
          }`}>
            {progress.progress >= 50 ? '✓' : ''} Extract
          </div>
          <div className={`text-center p-2 rounded text-xs ${
            progress.progress >= 75 ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-600'
          }`}>
            {progress.progress >= 75 ? '✓' : ''} Parse
          </div>
          <div className={`text-center p-2 rounded text-xs ${
            isCompleted ? 'bg-green-100 text-green-800 animate-pulse' : 
            isFailed ? 'bg-red-100 text-red-800' :
            progress.progress >= 100 ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-600'
          }`}>
            {isCompleted ? '🎉' : isFailed ? '❌' : progress.progress >= 100 ? '✓' : ''} Complete
          </div>
        </div>
        
        {/* Show completion celebration */}
        {isCompleted && (
          <div className="text-center p-3 bg-green-100 dark:bg-green-900/30 rounded-lg">
            <div className="text-2xl mb-1">🎉</div>
            <div className="text-sm font-medium text-green-800 dark:text-green-200">
              Processing Complete!
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};