
import React from 'react';
import { type Bureau } from '@/utils/bureau-constants';
import { Button } from "@/components/ui/button";
import { Download, Printer } from "lucide-react";

interface DisputeLetterPreviewProps {
  letterContent: string;
  bureau?: Bureau;
}

export function DisputeLetterPreview({ letterContent, bureau }: DisputeLetterPreviewProps) {
  const printLetter = () => {
    const printWindow = window.open('', '_blank');
    if (printWindow) {
      printWindow.document.write(`
        <html>
          <head>
            <title>Dispute Letter - ${bureau || 'Credit Bureau'}</title>
            <style>
              body {
                font-family: Arial, sans-serif;
                line-height: 1.5;
                margin: 40px;
              }
              pre {
                white-space: pre-wrap;
                font-family: Arial, sans-serif;
                font-size: 12pt;
              }
            </style>
          </head>
          <body>
            <pre>${letterContent}</pre>
          </body>
        </html>
      `);
      printWindow.document.close();
      printWindow.focus();
      setTimeout(() => {
        printWindow.print();
      }, 250);
    }
  };

  const downloadLetter = () => {
    const element = document.createElement("a");
    const file = new Blob([letterContent], { type: 'text/plain' });
    element.href = URL.createObjectURL(file);
    element.download = `Dispute_Letter_${bureau || 'Credit_Bureau'}_${new Date().toISOString().split('T')[0]}.txt`;
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  return (
    <div className="relative">
      <div className="absolute right-2 top-2 flex gap-2">
        <Button
          variant="outline"
          size="sm"
          className="h-8 px-2"
          onClick={downloadLetter}
        >
          <Download className="h-4 w-4 mr-1" />
          Download
        </Button>
        <Button
          variant="outline" 
          size="sm"
          className="h-8 px-2"
          onClick={printLetter}
        >
          <Printer className="h-4 w-4 mr-1" />
          Print
        </Button>
      </div>
      <div className="border p-8 rounded-md bg-white text-black font-mono text-sm whitespace-pre-wrap">
        {letterContent}
      </div>
    </div>
  );
}
