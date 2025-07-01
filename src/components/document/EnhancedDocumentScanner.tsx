
import { useState } from "react"
import { Button } from "@/components/ui/button"
import {
  Card, CardContent, CardDescription, CardHeader, CardTitle,
} from "@/components/ui/card"
import {
  Alert, AlertDescription, AlertTitle,
} from "@/components/ui/alert"
import {
  Tabs, TabsList, TabsTrigger, TabsContent,
} from "@/components/ui/tabs"
import { Badge } from "@/components/ui/badge"
import {
  Loader2, FileText, CheckCircle2, AlertCircle, Bot,
} from "lucide-react"
import { useToast } from "@/hooks/use-toast"
import { supabase } from "@/integrations/supabase/client"
import { useAuth } from "@/hooks/use-auth"
import { FileUploadZone } from "./FileUploadZone"
import type { NegativeItem } from "@/types/negative-item"
import { aiService, ExtractedText, DisputeAnalysis } from "@/utils/ai-service"

interface EnhancedDocumentScannerProps {
  onScanComplete: (negativeItems: NegativeItem[], analysis?: DisputeAnalysis) => void;
}

export function EnhancedDocumentScanner({ onScanComplete }: EnhancedDocumentScannerProps) {
  const [file, setFile] = useState<File | null>(null)
  const [isScanning, setIsScanning] = useState(false)
  const [scanStatus, setScanStatus] = useState<'idle' | 'uploading' | 'extracting' | 'analyzing' | 'complete' | 'error'>('idle')
  const [activeTab, setActiveTab] = useState<"upload" | "scan" | "analyze">("upload")
  const [disputeAnalysis, setDisputeAnalysis] = useState<DisputeAnalysis | null>(null)
  const [processingProgress, setProcessingProgress] = useState(0)
  const [processingStep, setProcessingStep] = useState('')
  const { toast } = useToast()
  const { user } = useAuth()

  const updateProgress = (step: string, progress: number) => {
    setProcessingStep(step)
    setProcessingProgress(progress)
  }

  const handleScan = async () => {
    if (!file || !user) {
      toast({
        title: "Error",
        description: "Please upload a file first",
        variant: "destructive",
      })
      return
    }

    setIsScanning(true)
    setScanStatus("uploading")
    updateProgress("Uploading document", 10)

    try {
      const userId = user.id
      const filePath = `${userId}/${Date.now()}_${file.name}`

      const { error: uploadError, data } = await supabase.storage
        .from("credit_reports")
        .upload(filePath, file, { cacheControl: "3600", upsert: false })

      if (uploadError) throw uploadError

      const fileUrl = supabase.storage
        .from("credit_reports")
        .getPublicUrl(data.path).data.publicUrl

      if (!fileUrl) throw new Error("Failed to get file URL")

      updateProgress("Extracting text from document", 30)
      setScanStatus("extracting")

      const extractedData = await aiService.extractTextFromDocument(fileUrl, file.type)

      updateProgress("Analyzing credit report", 60)
      setScanStatus("analyzing")

      const analysis = await aiService.analyzeReport(extractedData)
      setDisputeAnalysis(analysis)

      updateProgress("Analysis complete", 100)
      setScanStatus("complete")
      setIsScanning(false)
      setActiveTab("analyze")

      const negativeItems: NegativeItem[] = analysis.negativeItems.map(item => ({
        id: item.id,
        creditorName: item.creditorName,
        accountNumber: item.accountNumber,
        accountType: item.accountType as any,
        balance: item.balance,
        isNegative: item.isNegative,
        amount: item.amount,
        dateReported: item.dateReported,
        bureaus: item.bureaus,
        reason: item.reason || "Account disputed",
        status: item.status,
      }))

      onScanComplete(negativeItems, analysis)
      toast({
        title: "Analysis Complete",
        description: `Found ${negativeItems.length} negative items on your credit report.`,
      })
    } catch (error) {
      console.error("Scan failed:", error)
      setScanStatus("error")
      setIsScanning(false)
      toast({
        title: "Scan Failed",
        description: "There was an error analyzing your document. Please try again.",
        variant: "destructive",
      })
    }
  }

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center gap-2">
          <CardTitle>AI-Powered Credit Report Scanner</CardTitle>
          <Badge variant="outline" className="bg-blue-100 text-blue-800">
            <Bot className="h-3 w-3 mr-1" />
            AI Powered
          </Badge>
        </div>
        <CardDescription>
          Upload your credit report to scan for negative items with advanced AI analysis
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Tabs value={activeTab} onValueChange={(value) => setActiveTab(value as "upload" | "scan" | "analyze")} className="w-full">
          <TabsList className="grid grid-cols-3 mb-4">
            <TabsTrigger value="upload">Upload Document</TabsTrigger>
            <TabsTrigger value="scan" disabled={!file}>Process & Scan</TabsTrigger>
            <TabsTrigger value="analyze" disabled={!disputeAnalysis}>Analysis Results</TabsTrigger>
          </TabsList>

          <TabsContent value="upload">
            <FileUploadZone
              file={file}
              onFileChange={(newFile) => {
                setFile(newFile)
                if (newFile) setActiveTab("scan")
              }}
            />
          </TabsContent>

          <TabsContent value="scan">
            {file && (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-lg font-semibold">Document Processing</h3>
                    <p className="text-sm text-muted-foreground">
                      Our AI will extract and analyze your credit report
                    </p>
                  </div>
                  <Badge variant={isScanning ? "outline" : "default"} className="text-xs">
                    {isScanning ? (
                      <span className="flex items-center">
                        <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                        Processing...
                      </span>
                    ) : scanStatus === "complete" ? (
                      <span className="flex items-center">
                        <CheckCircle2 className="h-3 w-3 mr-1" />
                        Complete
                      </span>
                    ) : "Ready"}
                  </Badge>
                </div>

                {scanStatus === "error" ? (
                  <Alert variant="destructive">
                    <AlertCircle className="h-4 w-4" />
                    <AlertTitle>Error</AlertTitle>
                    <AlertDescription>
                      We encountered an error while processing your document. Please try again or upload a different document.
                    </AlertDescription>
                  </Alert>
                ) : (
                  <>
                    <div className="text-sm space-y-2">
                      <div className="flex justify-between">
                        <span>AI Processing Progress</span>
                        <span>{processingProgress}%</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2.5">
                        <div
                          className="bg-blue-600 h-2.5 rounded-full transition-all duration-300 ease-in-out"
                          style={{ width: `${processingProgress}%` }}
                        />
                      </div>
                      {processingStep && (
                        <p className="text-xs text-muted-foreground">Current step: {processingStep}</p>
                      )}
                    </div>

                    {!isScanning && scanStatus !== "complete" && (
                      <Button
                        onClick={handleScan}
                        className="w-full"
                        disabled={isScanning}
                      >
                        <FileText className="mr-2 h-4 w-4" />
                        Start AI Analysis
                      </Button>
                    )}

                    {scanStatus === "complete" && (
                      <Button
                        onClick={() => setActiveTab("analyze")}
                        variant="outline"
                        className="w-full"
                      >
                        View Analysis Results
                      </Button>
                    )}
                  </>
                )}
              </div>
            )}
          </TabsContent>

          <TabsContent value="analyze">
            {disputeAnalysis && (
              <div className="space-y-4">
                <div className="bg-blue-50 p-4 rounded-md border border-blue-200">
                  <h3 className="text-lg font-semibold flex items-center gap-2">
                    <Bot className="h-4 w-4" />
                    AI Analysis Summary
                  </h3>
                  <p className="mt-2 text-sm">
                    Identified {disputeAnalysis.negativeItems.length} negative items, of which{" "}
                    {disputeAnalysis.recommendedDisputes.length} are recommended for dispute.
                  </p>
                  {disputeAnalysis.recommendedDisputes.length > 0 && (
                    <div className="mt-2">
                      <p className="text-sm font-medium">Top dispute recommendations:</p>
                      <ul className="list-disc pl-5 text-sm mt-1 space-y-1">
                        {disputeAnalysis.recommendedDisputes.slice(0, 3).map((item, index) => (
                          <li key={index}>
                            {item.creditorName}: {item.recommendedReason}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>

                <div className="flex justify-end">
                  <Button
                    onClick={() => onScanComplete(
                      disputeAnalysis.negativeItems.map(item => ({
                        id: item.id,
                        creditorName: item.creditorName,
                        accountNumber: item.accountNumber,
                        accountType: item.accountType as any,
                        balance: item.balance,
                        isNegative: item.isNegative,
                        amount: item.amount,
                        dateReported: item.dateReported,
                        bureaus: item.bureaus,
                        reason: item.reason || "Account disputed",
                        status: item.status,
                      })),
                      disputeAnalysis
                    )}
                  >
                    Continue to Dispute Selection
                  </Button>
                </div>
              </div>
            )}
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  )
}
export default EnhancedDocumentScanner;
