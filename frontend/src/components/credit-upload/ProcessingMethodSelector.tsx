
import React from 'react';
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";

interface ProcessingMethodSelectorProps {
  processingMethod: 'ocr' | 'ai' | 'edge-function';
  onMethodChange: (method: 'ocr' | 'ai' | 'edge-function') => void;
}

export const ProcessingMethodSelector: React.FC<ProcessingMethodSelectorProps> = ({
  processingMethod,
  onMethodChange
}) => {
  return (
    <div>
      <Label htmlFor="processing-method" className="mb-2 block">Processing Method</Label>
      <div className="flex gap-4 mb-4">
        <Button
          variant={processingMethod === 'ocr' ? 'default' : 'outline'}
          onClick={() => onMethodChange('ocr')}
        >
          OCR (Fast)
        </Button>
        <Button
          variant={processingMethod === 'ai' ? 'default' : 'outline'}
          onClick={() => onMethodChange('ai')}
        >
          AI Analysis (Advanced)
        </Button>
        <Button
          variant={processingMethod === 'edge-function' ? 'default' : 'outline'}
          onClick={() => onMethodChange('edge-function')}
        >
          Edge Function (Document AI)
        </Button>
      </div>
    </div>
  );
};
