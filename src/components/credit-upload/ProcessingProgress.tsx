import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Loader2, FileText, Brain, Eye } from 'lucide-react';
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
  if (!isProcessing) {
    return null;
  }

  const getIcon = () => {
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
    switch (processingMethod) {
      case 'ocr':
        return 'OCR Processing';
      case 'ai':
        return 'AI Analysis';
      default:
        return 'Processing';
    }
  };

  return (
    <Card className="border-blue-200 bg-blue-50 dark:bg-blue-900/20">
      <CardHeader className="pb-3">
        <CardTitle className="text-lg flex items-center gap-2">
          {getIcon()}
          {getMethodLabel()}
          <Badge variant="secondary" className="ml-auto">
            {progress.progress}%
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">{progress.step}</span>
            <Loader2 className="h-4 w-4 animate-spin" />
          </div>
          <Progress value={progress.progress} className="w-full" />
          <p className="text-sm text-muted-foreground">{progress.message}</p>
        </div>
        
        {/* Processing stages indicator */}
        <div className="grid grid-cols-4 gap-2 mt-4">
          <div className={`text-center p-2 rounded text-xs ${
            progress.progress >= 25 ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-600'
          }`}>
            Initialize
          </div>
          <div className={`text-center p-2 rounded text-xs ${
            progress.progress >= 50 ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-600'
          }`}>
            Extract
          </div>
          <div className={`text-center p-2 rounded text-xs ${
            progress.progress >= 75 ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-600'
          }`}>
            Parse
          </div>
          <div className={`text-center p-2 rounded text-xs ${
            progress.progress >= 100 ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-600'
          }`}>
            Complete
          </div>
        </div>
      </CardContent>
    </Card>
  );
};