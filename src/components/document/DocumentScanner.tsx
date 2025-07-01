
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Loader2, FileText, Upload } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { type NegativeItem } from "@/types/negative-item";

interface DocumentScannerProps {
  onScanComplete: (negativeItems: NegativeItem[]) => void;
}

export function DocumentScanner({ onScanComplete }: DocumentScannerProps) {
  const [file, setFile] = useState<File | null>(null);
  const [isScanning, setIsScanning] = useState(false);
  const [scanResult, setScanResult] = useState<string>("");
  const { toast } = useToast();

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = event.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
      setScanResult("");
    }
  };

  const handleScan = async () => {
    if (!file) {
      toast({
        title: "No File Selected",
        description: "Please select a file to scan first.",
        variant: "destructive"
      });
      return;
    }

    setIsScanning(true);
    
    try {
      // Mock scanning process
      await new Promise(resolve => setTimeout(resolve, 3000));
      
      // Mock negative items found
      const mockNegativeItems: NegativeItem[] = [
        {
          id: "1",
          creditorName: "Capital One",
          accountNumber: "****1234",
          accountType: "credit_card",
          balance: 1500,
          isNegative: true,
          amount: "$1,500",
          dateReported: "2023-01-15",
          bureaus: ["Experian", "Equifax"],
          reason: "Charged Off",
          status: "charged_off"
        }
      ];

      setScanResult(`Found ${mockNegativeItems.length} negative items`);
      onScanComplete(mockNegativeItems);
      
      toast({
        title: "Scan Complete",
        description: `Found ${mockNegativeItems.length} negative items on your credit report.`,
      });
    } catch (error) {
      console.error("Scan failed:", error);
      toast({
        title: "Scan Failed",
        description: "There was an error scanning your document. Please try again.",
        variant: "destructive"
      });
    } finally {
      setIsScanning(false);
    }
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>Document Scanner</CardTitle>
        <CardDescription>
          Upload your credit report to scan for negative items
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
          <input
            type="file"
            onChange={handleFileChange}
            accept=".pdf,.jpg,.jpeg,.png"
            className="hidden"
            id="file-upload"
          />
          <label htmlFor="file-upload" className="cursor-pointer">
            <Upload className="mx-auto h-12 w-12 text-gray-400" />
            <p className="mt-2 text-sm text-gray-600">
              Click to upload or drag and drop
            </p>
            <p className="text-xs text-gray-500">
              PDF, JPG, PNG up to 10MB
            </p>
          </label>
        </div>

        {file && (
          <Alert>
            <FileText className="h-4 w-4" />
            <AlertDescription>
              Selected file: {file.name}
            </AlertDescription>
          </Alert>
        )}

        <Button 
          onClick={handleScan}
          disabled={!file || isScanning}
          className="w-full"
        >
          {isScanning ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Scanning...
            </>
          ) : (
            <>
              <FileText className="mr-2 h-4 w-4" />
              Scan Document
            </>
          )}
        </Button>

        {scanResult && (
          <Alert>
            <AlertDescription>
              {scanResult}
            </AlertDescription>
          </Alert>
        )}
      </CardContent>
    </Card>
  );
}
