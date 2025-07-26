
import { useState, useCallback, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2 } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { supabase } from "../../../supabase/client";
import { useAuth } from "@/hooks/use-auth";
import { FileUploadZone } from "./FileUploadZone";
import { ScanStatus } from "./ScanStatus";
import type { NegativeItem } from "@/types/document";

interface DocumentScannerProps {
  onScanComplete: (negativeItems: NegativeItem[]) => void;
}

export function DocumentScanner({ onScanComplete }: DocumentScannerProps) {
  const [file, setFile] = useState<File | null>(null);
  const [isScanning, setIsScanning] = useState(false);
  const [scanStatus, setScanStatus] = useState<'idle' | 'scanning' | 'complete' | 'error'>('idle');
  const { toast } = useToast();
  const { user } = useAuth();

  const handleScan = async () => {
    if (!file) {
      toast({
        title: "Error",
        description: "Please upload a file first",
        variant: "destructive"
      });
      return;
    }

    setIsScanning(true);
    setScanStatus('scanning');

    try {
      const userId = user?.id || 'anonymous';
      const filePath = `${userId}/${Date.now()}_${file.name}`;
      
      console.log('Uploading file to:', filePath);
      
      if (user) {
        const { error: uploadError, data } = await supabase.storage
          .from('credit_reports')
          .upload(filePath, file, {
            cacheControl: '3600',
            upsert: false
          });

        if (uploadError) {
          console.error('Upload error:', uploadError);
          throw uploadError;
        }

        console.log('File uploaded successfully:', data?.path);
      }

      // Simulate document analysis with mock data
      setTimeout(() => {
        const mockNegativeItems: NegativeItem[] = [
          {
            id: "1",
            creditorName: "ABC Collections",
            accountNumber: "XXXX-1234",
            amount: "$1,245",
            dateReported: "2024-03-15",
            bureaus: ["Experian", "TransUnion"],
            reason: "Collection Account",
            status: "Open"
          },
          {
            id: "2",
            creditorName: "XYZ Financial",
            accountNumber: "XXXX-5678",
            amount: "$567",
            dateReported: "2024-02-20",
            bureaus: ["Equifax", "Experian"],
            reason: "Late Payment",
            status: "Open"
          },
          {
            id: "3",
            creditorName: "Credit Card Company",
            accountNumber: "XXXX-9012",
            amount: "$3,500",
            dateReported: "2024-01-10",
            bureaus: ["TransUnion", "Equifax"],
            reason: "Charge-off",
            status: "Open"
          }
        ];

        setScanStatus('complete');
        setIsScanning(false);
        onScanComplete(mockNegativeItems);
        
        toast({
          title: "Analysis Complete",
          description: `Found ${mockNegativeItems.length} negative items on your credit report.`,
        });
      }, 3000);
    } catch (error) {
      console.error("Error scanning document:", error);
      setScanStatus('error');
      setIsScanning(false);
      toast({
        title: "Scan Failed",
        description: "There was an error analyzing your document. Please try again.",
        variant: "destructive"
      });
    }
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>Upload Credit Report</CardTitle>
        <CardDescription>
          Upload your credit report to scan for negative items that can be disputed
        </CardDescription>
      </CardHeader>
      <CardContent>
        <FileUploadZone file={file} onFileChange={setFile} />
        
        <ScanStatus status={scanStatus} />

        {file && scanStatus !== 'scanning' && (
          <div className="mt-4 flex justify-center">
            <Button 
              onClick={handleScan}
              size="sm"
              disabled={isScanning}
            >
              {isScanning ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Scanning
                </>
              ) : (
                "Scan Document"
              )}
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
