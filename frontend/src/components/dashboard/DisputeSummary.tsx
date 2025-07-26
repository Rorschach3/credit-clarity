
import { useState } from "react";
import { Card, CardHeader, CardContent, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ChevronRight } from "lucide-react";
import { NegativeItemsDialog } from "./NegativeItemsDialog";

export function DisputeSummary() {
  const [isDialogOpen, setIsDialogOpen] = useState(false);

  return (
    <>
      <Card className="cursor-pointer hover:border-primary transition-colors" onClick={() => setIsDialogOpen(true)}>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            Dispute Summary
            <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
              <ChevronRight className="h-4 w-4" />
            </Button>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex justify-between">
              <span className="text-gray-600">Total Items</span>
              <span className="font-medium">12</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Disputed</span>
              <span className="font-medium">8</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Removed</span>
              <span className="font-medium text-green-600">3</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">In Progress</span>
              <span className="font-medium text-yellow-600">5</span>
            </div>
          </div>
        </CardContent>
      </Card>

      <NegativeItemsDialog open={isDialogOpen} onOpenChange={setIsDialogOpen} />
    </>
  );
}
