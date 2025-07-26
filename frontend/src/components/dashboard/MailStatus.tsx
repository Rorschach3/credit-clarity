
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardContent, CardFooter, CardTitle } from "@/components/ui/card";
import { Clock, CheckCircle2 } from "lucide-react";

interface MailStatusProps {
  onBackToOverview: () => void;
}

export function MailStatus({ onBackToOverview }: MailStatusProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Mail Status</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div>
            <h3 className="font-semibold mb-1">Ready to Send</h3>
            <p className="text-sm flex justify-between">
              <span>Experian</span>
              <Button variant="outline" size="sm">Send Now</Button>
            </p>
          </div>
          
          <div>
            <h3 className="font-semibold mb-1">In Transit</h3>
            <p className="text-sm flex items-center justify-between">
              <span>TransUnion</span>
              <span className="text-yellow-600 flex items-center">
                <Clock className="h-3 w-3 mr-1" /> 2 days
              </span>
            </p>
          </div>
          
          <div>
            <h3 className="font-semibold mb-1">Delivered</h3>
            <p className="text-sm flex items-center justify-between">
              <span>Equifax</span>
              <span className="text-green-600 flex items-center">
                <CheckCircle2 className="h-3 w-3 mr-1" /> Apr 12
              </span>
            </p>
          </div>
        </div>
      </CardContent>
      <CardFooter>
        <Button variant="outline" onClick={onBackToOverview} className="w-full">
          Back to Overview
        </Button>
      </CardFooter>
    </Card>
  );
}
