
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Bot } from "lucide-react";

interface AiAlertProps {
  recommendationsCount: number;
}

export function AiAlert({ recommendationsCount }: AiAlertProps) {
  return (
    <Alert className="mb-4 bg-blue-50 border-blue-200">
      <Bot className="h-4 w-4" />
      <AlertDescription>
        Our AI has analyzed your report and identified {recommendationsCount} items 
        with high dispute potential. These items are pre-selected below.
      </AlertDescription>
    </Alert>
  );
}
