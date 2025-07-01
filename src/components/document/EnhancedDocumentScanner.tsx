import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { CheckCircle, XCircle, Upload, FileText, AlertCircle } from "lucide-react";
import { NegativeItem } from "@/types/negative-item";
import { aiService, type Account, type DisputeAnalysis } from "@/utils/ai-service";

interface EnhancedDocumentScannerProps {
  onNegativeItemsFound: (items: NegativeItem[], analysis?: DisputeAnalysis) => void;
}

export function EnhancedDocumentScanner({ 
  onNegativeItemsFound
}: EnhancedDocumentScannerProps) {
  const [uploadProgress, setUploadProgress] = useState(0);
  const [scanStatus, setScanStatus] = useState<'idle' | 'uploading' | 'processing' | 'complete' | 'error'>('idle');
  const [errorMessage, setErrorMessage] = useState<string>('');
  const [fileName, setFileName] = useState<string>('');
  const [processingStep, setProcessingStep] = useState<string>('');

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (file.type !== 'application/pdf') {
      setErrorMessage('Please upload a PDF file only');
      setScanStatus('error');
      return;
    }

    if (file.size > 10 * 1024 * 1024) { // 10MB limit
      setErrorMessage('File size must be less than 10MB');
      setScanStatus('error');
      return;
    }

    setFileName(file.name);
    setScanStatus('uploading');
    setErrorMessage('');
    setUploadProgress(0);

    // Simulate upload progress
    const uploadInterval = setInterval(() => {
      setUploadProgress(prev => {
        if (prev >= 100) {
          clearInterval(uploadInterval);
          processDocument(file);
          return 100;
        }
        return prev + 10;
      });
    }, 200);
  };

  const processDocument = async (file: File) => {
    try {
      setScanStatus('processing');
      setProcessingStep('Extracting text from document...');
      setUploadProgress(0);

      // Create a file URL for processing
      const fileUrl = URL.createObjectURL(file);
      
      // Step 1: Extract text (25% progress)
      setUploadProgress(25);
      const extractedText = await aiService.extractTextFromDocument(fileUrl, file.type);
      
      // Step 2: Analyze for negative items (75% progress)
      setProcessingStep('Analyzing credit report for negative items...');
      setUploadProgress(75);
      const analysis = await aiService.analyzeReport(extractedText);
      
      // Step 3: Format results (100% progress)
      setProcessingStep('Formatting results...');
      setUploadProgress(100);
      
      // Convert AI service accounts to NegativeItem format
      const negativeItems: NegativeItem[] = analysis.negativeItems.map((item: Account) => ({
        id: item.id,
        creditorName: item.creditorName,
        accountNumber: item.accountNumber,
        accountType: item.accountType,
        balance: item.balance,
        isNegative: item.isNegative,
        amount: item.amount,
        dateReported: item.dateReported,
        bureaus: item.bureaus,
        reason: item.reason || "Negative item detected",
        status: item.status
      }));

      // Clean up the object URL
      URL.revokeObjectURL(fileUrl);
      
      setScanStatus('complete');
      onNegativeItemsFound(negativeItems, analysis);

    } catch (error) {
      console.error('Error processing document:', error);
      setErrorMessage('Failed to process document. Please try again.');
      setScanStatus('error');
    }
  };

  const resetScanner = () => {
    setScanStatus('idle');
    setUploadProgress(0);
    setErrorMessage('');
    setFileName('');
    setProcessingStep('');
  };

  const renderStatus = () => {
    switch (scanStatus) {
      case 'idle':
        return (
          <div className="text-center py-8">
            <Upload className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-medium mb-2">Upload Credit Report</h3>
            <p className="text-muted-foreground mb-4">
              Drag and drop your PDF credit report or click to browse
            </p>
            <input
              type="file"
              accept=".pdf"
              onChange={handleFileUpload}
              className="hidden"
              id="file-upload"
            />
            <label htmlFor="file-upload">
              <Button asChild className="cursor-pointer">
                <span>Choose File</span>
              </Button>
            </label>
          </div>
        );

      case 'uploading':
        return (
          <div className="text-center py-8">
            <FileText className="mx-auto h-12 w-12 text-blue-500 mb-4" />
            <h3 className="text-lg font-medium mb-2">Uploading {fileName}</h3>
            <Progress value={uploadProgress} className="w-full max-w-sm mx-auto mb-2" />
            <p className="text-sm text-muted-foreground">{uploadProgress}% complete</p>
          </div>
        );

      case 'processing':
        return (
          <div className="text-center py-8">
            <div className="animate-spin mx-auto h-12 w-12 border-4 border-blue-500 border-t-transparent rounded-full mb-4"></div>
            <h3 className="text-lg font-medium mb-2">Processing Document</h3>
            <Progress value={uploadProgress} className="w-full max-w-sm mx-auto mb-2" />
            <p className="text-sm text-muted-foreground">{processingStep}</p>
          </div>
        );

      case 'complete':
        return (
          <div className="text-center py-8">
            <CheckCircle className="mx-auto h-12 w-12 text-green-500 mb-4" />
            <h3 className="text-lg font-medium mb-2">Processing Complete</h3>
            <p className="text-muted-foreground mb-4">
              Successfully analyzed your credit report
            </p>
            <Button onClick={resetScanner} variant="outline">
              Upload Another Report
            </Button>
          </div>
        );

      case 'error':
        return (
          <div className="text-center py-8">
            <XCircle className="mx-auto h-12 w-12 text-red-500 mb-4" />
            <h3 className="text-lg font-medium mb-2">Processing Failed</h3>
            <Alert className="mb-4">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{errorMessage}</AlertDescription>
            </Alert>
            <Button onClick={resetScanner}>Try Again</Button>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>Credit Report Scanner</CardTitle>
      </CardHeader>
      <CardContent>
        {renderStatus()}
        
        {scanStatus === 'complete' && (
          <div className="mt-6 p-4 bg-blue-50 rounded-lg">
            <h4 className="font-medium text-blue-900 mb-2">What happens next?</h4>
            <ul className="text-sm text-blue-800 space-y-1">
              <li>• Review the negative items found in your report</li>
              <li>• Select which items you want to dispute</li>
              <li>• Generate professional dispute letters</li>
              <li>• Track your dispute progress</li>
            </ul>
          </div>
        )}

        {scanStatus === 'idle' && (
          <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4 text-center">
            <div className="p-3 bg-gray-50 rounded-lg">
              <FileText className="mx-auto h-8 w-8 text-blue-500 mb-2" />
              <h4 className="font-medium mb-1">PDF Only</h4>
              <p className="text-xs text-muted-foreground">Upload PDF credit reports from any bureau</p>
            </div>
            <div className="p-3 bg-gray-50 rounded-lg">
              <AlertCircle className="mx-auto h-8 w-8 text-green-500 mb-2" />
              <h4 className="font-medium mb-1">AI Analysis</h4>
              <p className="text-xs text-muted-foreground">Advanced AI finds disputable items</p>
            </div>
            <div className="p-3 bg-gray-50 rounded-lg">
              <CheckCircle className="mx-auto h-8 w-8 text-purple-500 mb-2" />
              <h4 className="font-medium mb-1">Secure</h4>
              <p className="text-xs text-muted-foreground">Your data is processed securely</p>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
