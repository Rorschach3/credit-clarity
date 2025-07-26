import React from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { CheckCircle, Download, Upload } from "lucide-react";
import { type PacketProgress } from "@/utils/disputeUtils";

interface PacketGenerationSectionProps {
  isGenerating: boolean;
  generationProgress: PacketProgress;
  generatedPDF: Blob | null;
  documentsCompleted: boolean;
  onPreparePacket: () => void;
  onDownloadPDF: () => void;
  onClose: () => void;
}

export const PacketGenerationSection: React.FC<PacketGenerationSectionProps> = ({
  isGenerating,
  generationProgress,
  generatedPDF,
  documentsCompleted,
  onPreparePacket,
  onDownloadPDF,
  onClose
}) => {
  return (
    <Card className="mt-8">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Upload className="h-5 w-5" />
          Generate Final Dispute Packet
        </CardTitle>
        <CardDescription>
          Create your complete dispute packet ready for mailing to credit bureaus
        </CardDescription>
      </CardHeader>
      
      <CardContent className="space-y-6">
        {/* Status Check */}
        <div className="flex items-center gap-3 p-4 bg-green-50 border border-green-200 rounded-lg">
          <CheckCircle className="h-5 w-5 text-green-600" />
          <div>
            <p className="font-medium text-green-800">Ready to Generate Complete Packet</p>
            <p className="text-sm text-green-600">
              Letters generated • {documentsCompleted ? 'Documents uploaded' : 'Documents skipped'}
            </p>
            <p className="text-xs text-green-500 mt-1">
              Will include dispute letters + any uploaded documents (ID, SSN, utility bill)
            </p>
          </div>
        </div>

        {/* Generation Progress */}
        {isGenerating && (
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm font-medium">{generationProgress.step}</span>
              <span className="text-sm text-muted-foreground">{generationProgress.progress}%</span>
            </div>
            <Progress value={generationProgress.progress} className="w-full" />
            <p className="text-sm text-muted-foreground">{generationProgress.message}</p>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-3">
          {!isGenerating && generationProgress.progress < 100 && (
            <Button 
              onClick={onPreparePacket}
              className="flex-1"
              size="lg"
            >
              <Upload className="h-4 w-4 mr-2" />
              Generate Complete Dispute Packet
            </Button>
          )}

          {generationProgress.progress === 100 && generatedPDF && (
            <Button 
              onClick={onDownloadPDF}
              className="flex-1"
              size="lg"
              variant="default"
            >
              <Download className="h-4 w-4 mr-2" />
              Download Complete Packet
            </Button>
          )}

          <Button 
            variant="outline" 
            onClick={onClose}
            disabled={isGenerating}
          >
            {generationProgress.progress === 100 ? 'Close' : 'Cancel'}
          </Button>
        </div>

        {/* Success Message */}
        {generationProgress.progress === 100 && (
          <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
            <p className="font-medium text-green-800">Complete Dispute Packet Ready!</p>
            <p className="text-sm text-green-600 mt-1">
              Your complete dispute packet has been generated and includes all dispute letters plus any uploaded documents (ID, SSN card, utility bill).
            </p>
            <p className="text-sm text-green-600 mt-2">
              📋 Next steps: Download, print, sign, and mail with certified mail to each credit bureau.
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
};