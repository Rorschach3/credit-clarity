
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardContent, CardFooter, CardTitle } from "@/components/ui/card";

interface UploadTipsProps {
  onBackToOverview: () => void;
}

export function UploadTips({ onBackToOverview }: UploadTipsProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Upload Tips</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div>
            <h3 className="font-semibold mb-1">Get Official Reports</h3>
            <p className="text-sm text-gray-600">
              Download official reports from annualcreditreport.com or directly from each bureau.
            </p>
          </div>
          
          <div>
            <h3 className="font-semibold mb-1">Complete Reports</h3>
            <p className="text-sm text-gray-600">
              Make sure to upload the full report, including all pages.
            </p>
          </div>
          
          <div>
            <h3 className="font-semibold mb-1">High Quality Images</h3>
            <p className="text-sm text-gray-600">
              If uploading scans or photos, ensure they are clear and readable.
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
