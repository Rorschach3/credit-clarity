import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2, FileText, Bug, CheckCircle, XCircle } from 'lucide-react';
import { toast } from 'sonner';

interface DebugResult {
  text_length: number;
  first_500_chars: string;
  methods: {
    gemini?: {
      tradelines: any[];
      count: number;
      error?: string;
    };
    basic?: {
      tradelines: any[];
      count: number;
      error?: string;
    };
  };
}

const PDFDebugger: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [method, setMethod] = useState<string>('all');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<DebugResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
      setResult(null);
      setError(null);
    }
  };

  const handleDebugParsing = async () => {
    if (!file) {
      toast.error('Please select a PDF file first');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('method', method);

      const response = await fetch('http://localhost:8000/debug-parsing', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: DebugResult = await response.json();
      setResult(data);
      toast.success('Debug parsing completed successfully');
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'An error occurred';
      setError(errorMessage);
      toast.error(`Debug parsing failed: ${errorMessage}`);
    } finally {
      setLoading(false);
    }
  };

  const renderMethodResult = (methodName: string, methodResult: any) => {
    if (!methodResult) return null;

    const hasError = methodResult.error;
    const count = methodResult.count || 0;

    return (
      <div className="space-y-3">
        <div className="flex items-center gap-2">
          <h4 className="font-medium capitalize">{methodName} Method</h4>
          <Badge variant={hasError ? "destructive" : "default"}>
            {hasError ? <XCircle className="h-3 w-3 mr-1" /> : <CheckCircle className="h-3 w-3 mr-1" />}
            {count} tradelines
          </Badge>
        </div>

        {hasError && (
          <Alert variant="destructive">
            <AlertDescription>
              Error: {methodResult.error}
            </AlertDescription>
          </Alert>
        )}

        {!hasError && methodResult.tradelines && methodResult.tradelines.length > 0 && (
          <div className="space-y-2">
            <Label className="text-sm font-medium">Extracted Tradelines:</Label>
            <div className="max-h-64 overflow-y-auto">
              {methodResult.tradelines.map((tradeline: any, index: number) => (
                <Card key={index} className="p-3 mb-2">
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div>
                      <Label className="font-medium">Creditor:</Label>
                      <p className="truncate">{tradeline.creditor_name || 'N/A'}</p>
                    </div>
                    <div>
                      <Label className="font-medium">Account Type:</Label>
                      <p className="truncate">{tradeline.account_type || 'N/A'}</p>
                    </div>
                    <div>
                      <Label className="font-medium">Balance:</Label>
                      <p className="truncate">{tradeline.account_balance || 'N/A'}</p>
                    </div>
                    <div>
                      <Label className="font-medium">Status:</Label>
                      <p className="truncate">{tradeline.account_status || 'N/A'}</p>
                    </div>
                    <div>
                      <Label className="font-medium">Account #:</Label>
                      <p className="truncate">{tradeline.account_number || 'N/A'}</p>
                    </div>
                    <div>
                      <Label className="font-medium">Date Opened:</Label>
                      <p className="truncate">{tradeline.date_opened || 'N/A'}</p>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          </div>
        )}

        {!hasError && (!methodResult.tradelines || methodResult.tradelines.length === 0) && (
          <Alert>
            <AlertDescription>
              No tradelines extracted using {methodName} method
            </AlertDescription>
          </Alert>
        )}
      </div>
    );
  };

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Bug className="h-5 w-5" />
            PDF Parsing Debugger
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="file-upload">Select PDF File</Label>
              <Input
                id="file-upload"
                type="file"
                accept=".pdf"
                onChange={handleFileChange}
                disabled={loading}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="method-select">Parsing Method</Label>
              <Select value={method} onValueChange={setMethod} disabled={loading}>
                <SelectTrigger>
                  <SelectValue placeholder="Select method" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Methods</SelectItem>
                  <SelectItem value="gemini">Gemini AI Only</SelectItem>
                  <SelectItem value="basic">Basic Parsing Only</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <Button 
            onClick={handleDebugParsing} 
            disabled={!file || loading}
            className="w-full"
          >
            {loading ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Processing...
              </>
            ) : (
              <>
                <FileText className="h-4 w-4 mr-2" />
                Debug PDF Parsing
              </>
            )}
          </Button>

          {file && (
            <div className="text-sm text-muted-foreground">
              Selected file: {file.name} ({(file.size / 1024 / 1024).toFixed(2)} MB)
            </div>
          )}
        </CardContent>
      </Card>

      {error && (
        <Alert variant="destructive">
          <XCircle className="h-4 w-4" />
          <AlertDescription>
            {error}
          </AlertDescription>
        </Alert>
      )}

      {result && (
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>PDF Analysis Results</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label className="font-medium">Text Length:</Label>
                  <p className="text-lg">{result.text_length.toLocaleString()} characters</p>
                </div>
                <div>
                  <Label className="font-medium">Total Methods Used:</Label>
                  <p className="text-lg">{Object.keys(result.methods).length}</p>
                </div>
              </div>

              <div className="space-y-2">
                <Label className="font-medium">First 500 Characters:</Label>
                <Textarea
                  value={result.first_500_chars}
                  readOnly
                  className="h-32 text-xs font-mono"
                />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Parsing Results by Method</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {result.methods.gemini && renderMethodResult('gemini', result.methods.gemini)}
              {result.methods.basic && renderMethodResult('basic', result.methods.basic)}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
};

export default PDFDebugger;