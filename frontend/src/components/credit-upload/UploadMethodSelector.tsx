import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Eye, Brain, FileText, Zap, Clock } from 'lucide-react';

interface UploadMethodSelectorProps {
  selectedMethod: 'ocr' | 'ai';
  onMethodChange: (method: 'ocr' | 'ai') => void;
  isProcessing: boolean;
}

export const UploadMethodSelector: React.FC<UploadMethodSelectorProps> = ({
  selectedMethod,
  onMethodChange,
  isProcessing
}) => {
  const methods = [
    {
      id: 'ocr' as const,
      name: 'OCR Processing',
      description: 'Fast text extraction from PDF files',
      icon: <Eye className="h-5 w-5" />,
      features: ['Quick processing', 'Basic text extraction', 'Good for simple reports'],
      badge: 'Fast',
      badgeVariant: 'secondary' as const,
      pros: ['Faster processing', 'Lower resource usage', 'Good for clear PDFs'],
      cons: ['May miss complex layouts', 'Less accurate for handwritten text']
    },
    {
      id: 'ai' as const,
      name: 'AI Analysis',
      description: 'Advanced AI-powered credit report analysis',
      icon: <Brain className="h-5 w-5" />,
      features: ['Advanced parsing', 'Structure recognition', 'High accuracy'],
      badge: 'Smart',
      badgeVariant: 'default' as const,
      pros: ['Higher accuracy', 'Better layout understanding', 'Handles complex formats'],
      cons: ['Slower processing', 'Requires internet connection']
    }
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg flex items-center gap-2">
          <FileText className="h-5 w-5" />
          Processing Method
        </CardTitle>
        <p className="text-sm text-muted-foreground">
          Choose how you want to process your credit report
        </p>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {methods.map((method) => (
            <div
              key={method.id}
              className={`relative p-4 border rounded-lg cursor-pointer transition-all ${
                selectedMethod === method.id
                  ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                  : 'border-gray-200 hover:border-gray-300'
              } ${isProcessing ? 'opacity-50 cursor-not-allowed' : ''}`}
              onClick={() => !isProcessing && onMethodChange(method.id)}
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-2">
                  {method.icon}
                  <h3 className="font-medium">{method.name}</h3>
                </div>
                <Badge variant={method.badgeVariant}>{method.badge}</Badge>
              </div>
              
              <p className="text-sm text-muted-foreground mb-3">
                {method.description}
              </p>
              
              <div className="space-y-2">
                <div>
                  <h4 className="text-xs font-medium text-green-700 dark:text-green-400 mb-1">
                    ✓ Advantages
                  </h4>
                  <ul className="text-xs text-muted-foreground space-y-1">
                    {method.pros.map((pro, index) => (
                      <li key={index}>• {pro}</li>
                    ))}
                  </ul>
                </div>
                
                <div>
                  <h4 className="text-xs font-medium text-orange-700 dark:text-orange-400 mb-1">
                    ⚠ Considerations
                  </h4>
                  <ul className="text-xs text-muted-foreground space-y-1">
                    {method.cons.map((con, index) => (
                      <li key={index}>• {con}</li>
                    ))}
                  </ul>
                </div>
              </div>
              
              {selectedMethod === method.id && (
                <div className="absolute top-2 right-2">
                  <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                </div>
              )}
            </div>
          ))}
        </div>
        
        <div className="mt-4 p-3 bg-gray-50 dark:bg-gray-900 rounded-lg">
          <div className="flex items-center gap-2 text-sm">
            {selectedMethod === 'ocr' ? (
              <>
                <Clock className="h-4 w-4 text-green-600" />
                <span className="text-green-700 dark:text-green-400 font-medium">
                  Estimated time: 30-60 seconds
                </span>
              </>
            ) : (
              <>
                <Zap className="h-4 w-4 text-blue-600" />
                <span className="text-blue-700 dark:text-blue-400 font-medium">
                  Estimated time: 2-5 minutes
                </span>
              </>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};