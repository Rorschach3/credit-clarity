
import { CheckCircle2, AlertTriangle, FileText } from "lucide-react";
import { Card, CardHeader, CardContent, CardTitle } from "@/components/ui/card";
import { ActivityItem } from "./ActivityItem";

export function RecentActivity() {
  return (
    <Card className="lg:col-span-2">
      <CardHeader>
        <CardTitle>Recent Activity</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <ActivityItem 
            icon={<CheckCircle2 className="h-5 w-5 text-green-600" />}
            iconBgClass="bg-green-100"
            title="Dispute letter sent to Experian"
            time="3 days ago"
          />
          
          <ActivityItem 
            icon={<AlertTriangle className="h-5 w-5 text-yellow-600" />}
            iconBgClass="bg-yellow-100"
            title="TransUnion requested additional information"
            time="5 days ago"
          />
          
          <ActivityItem 
            icon={<FileText className="h-5 w-5 text-blue-600" />}
            iconBgClass="bg-blue-100"
            title="Equifax report uploaded"
            time="1 week ago"
          />
        </div>
      </CardContent>
    </Card>
  );
}
