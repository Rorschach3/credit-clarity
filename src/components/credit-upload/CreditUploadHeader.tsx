import React from 'react';
import { CardHeader, CardTitle } from '@/components/ui/card';
import { Upload, FileText, Target, ArrowRight } from 'lucide-react';

interface CreditUploadHeaderProps {
  hasExistingTradelines?: boolean;
  tradelinesCount?: number;
}

export const CreditUploadHeader: React.FC<CreditUploadHeaderProps> = ({
  hasExistingTradelines = false,
  tradelinesCount = 0
}) => {
  return (
    <CardHeader className="text-center">
      <CardTitle className="text-2xl flex items-center justify-center gap-2">
        <Upload className="h-6 w-6" />
        {hasExistingTradelines ? 'Add More Credit Reports' : 'Upload Credit Reports'}
      </CardTitle>
      <div className="space-y-3">
        <p className="text-muted-foreground">
          {hasExistingTradelines 
            ? `You have ${tradelinesCount} tradelines. Upload additional reports to find more items to dispute.`
            : 'Upload your credit report PDFs to automatically extract tradeline information for dispute letters'
          }
        </p>
        
        <div className="flex items-center justify-center gap-4 text-sm">
          <div className="flex items-center gap-1 text-green-600">
            <FileText className="h-4 w-4" />
            <span>PDF Format</span>
          </div>
          <div className="flex items-center gap-1 text-blue-600">
            <span>•</span>
            <span>AI-Powered</span>
          </div>
          <div className="flex items-center gap-1 text-purple-600">
            <span>•</span>
            <span>Secure Processing</span>
          </div>
        </div>

        {/* Goal reminder */}
        <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-950/20 rounded-lg">
          <div className="flex items-center justify-center gap-2 text-blue-700 dark:text-blue-300">
            <Target className="h-4 w-4" />
            <span className="text-sm font-medium">Goal: Extract negative tradelines for dispute letters</span>
            <ArrowRight className="h-4 w-4" />
          </div>
        </div>
      </div>
    </CardHeader>
  );
};