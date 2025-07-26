
import { BarChart4 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardContent, CardTitle, CardDescription } from "@/components/ui/card";

interface CreditScoreProgressProps {
  onUploadReports: () => void;
}

export function CreditScoreProgress({ onUploadReports }: CreditScoreProgressProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Credit Score Progress</CardTitle>
        <CardDescription>
          Track your credit score improvements over time
        </CardDescription>
      </CardHeader>
      <CardContent className="h-80 flex items-center justify-center">
        <div className="text-center">
          <BarChart4 className="h-16 w-16 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium mb-2">Credit History Charts</h3>
          <p className="text-gray-500 mb-4">
            Your credit score history will appear here once you've uploaded your reports
          </p>
          <Button onClick={onUploadReports}>
            Upload Reports
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
