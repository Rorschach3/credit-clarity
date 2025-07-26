
import { AlertCircle, Check, Loader2 } from "lucide-react";

interface ScanStatusProps {
  status: 'idle' | 'scanning' | 'complete' | 'error';
}

export function ScanStatus({ status }: ScanStatusProps) {
  if (status === 'scanning') {
    return (
      <div className="mt-4 p-4 bg-primary-foreground rounded-lg">
        <div className="flex items-center mb-2">
          <Loader2 className="h-5 w-5 text-primary animate-spin mr-2" />
          <p className="text-sm font-medium">Analyzing document...</p>
        </div>
        <p className="text-xs text-gray-500">
          Our AI is scanning your document for negative items that can be disputed.
          This may take a moment.
        </p>
      </div>
    );
  }

  if (status === 'complete') {
    return (
      <div className="mt-4 p-4 bg-green-50 rounded-lg border border-green-100">
        <div className="flex items-center mb-1">
          <Check className="h-5 w-5 text-green-600 mr-2" />
          <p className="text-sm font-medium text-green-800">Analysis complete!</p>
        </div>
        <p className="text-xs text-green-700">
          Negative items identified. Scroll down to review them and generate disputes.
        </p>
      </div>
    );
  }

  if (status === 'error') {
    return (
      <div className="mt-4 p-4 bg-[rgba(255,255,255,0.08)] rounded-lg border border-red-100">
        <div className="flex items-center mb-1">
          <AlertCircle className="h-5 w-5 text-red-600 mr-2" />
          <p className="text-sm font-medium text-red-800">Analysis failed</p>
        </div>
        <p className="text-xs text-red-700">
          There was an error analyzing your document. Please try again or upload a different file.
        </p>
      </div>
    );
  }

  return null;
}
