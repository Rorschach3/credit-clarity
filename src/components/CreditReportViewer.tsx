
import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { FileText, Download } from "lucide-react";

interface CreditReportViewerProps {
  reportData: {
    fileName: string;
    uploadDate: string;
  };
}

const CreditReportViewer: React.FC<CreditReportViewerProps> = ({ reportData }) => {
  const [isLoading, setIsLoading] = useState(false);

  const handleDownload = async () => {
    setIsLoading(true);
    try {
      // Download logic would go here
      console.log('Downloading report:', reportData.fileName);
    } catch (error) {
      console.error('Error downloading report:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <FileText className="h-5 w-5" />
          Credit Report Viewer
        </CardTitle>
        <CardDescription>
          View and manage your uploaded credit report
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div>
            <p className="font-medium">File Name:</p>
            <p className="text-muted-foreground">{reportData.fileName}</p>
          </div>
          <div>
            <p className="font-medium">Upload Date:</p>
            <p className="text-muted-foreground">{reportData.uploadDate}</p>
          </div>
          <Button onClick={handleDownload} disabled={isLoading}>
            <Download className="h-4 w-4 mr-2" />
            Download Report
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};

export default CreditReportViewer;
