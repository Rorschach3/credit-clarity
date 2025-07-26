import React from 'react';
import { CardHeader, CardTitle } from '@/components/ui/card';
import { Upload, FileText } from 'lucide-react';

export const CreditUploadHeader: React.FC = () => {
  return (
    <CardHeader className="text-center">
      <CardTitle className="text-2xl flex items-center justify-center gap-2">
        <Upload className="h-6 w-6" />
        Credit Report Upload
      </CardTitle>
      <div className="space-y-2">
        <p className="text-muted-foreground">
          Upload your credit report PDF to automatically extract tradeline information
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
      </div>
    </CardHeader>
  );
};