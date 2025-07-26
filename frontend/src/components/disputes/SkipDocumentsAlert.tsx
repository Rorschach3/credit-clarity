
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { AlertCircle } from "lucide-react";

interface SkipDocumentsAlertProps {
  onSkip: () => void;
}

export function SkipDocumentsAlert({ onSkip }: SkipDocumentsAlertProps) {
  return (
    <Alert className="mt-6 bg-blue-50 border-blue-200">
      <AlertCircle className="h-4 w-4 text-blue-500" />
      <AlertDescription className="text-blue-700">
        Documents help verify your identity with credit bureaus, but you can continue without them if needed.
        <div className="mt-4">
          <Button 
            variant="outline"
            onClick={onSkip}
            className="bg-white hover:bg-blue-50"
          >
            Skip Documents & Continue to Letters
          </Button>
        </div>
      </AlertDescription>
    </Alert>
  );
}
