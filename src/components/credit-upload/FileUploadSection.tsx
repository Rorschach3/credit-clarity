
import React, { ChangeEvent } from 'react';
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Progress } from "@/components/ui/progress";

interface FileUploadSectionProps {
  onFileUpload: (event: ChangeEvent<HTMLInputElement>) => void;
  isUploading: boolean;
  uploadProgress: number;
  processingMethod: 'ocr' | 'ai';
}

export const FileUploadSection: React.FC<FileUploadSectionProps> = ({
  onFileUpload,
  isUploading,
  uploadProgress,
  processingMethod
}) => {
  return (
    <div>
      <Label htmlFor="pdf-upload">Upload Credit Report (PDF)</Label>
      <Input
        id="pdf-upload"
        type="file"
        accept="application/pdf"
        onChange={onFileUpload}
        disabled={isUploading}
      />
      {isUploading && (
        <div className="mt-2">
          <Progress value={uploadProgress} className="w-full" />
          <p className="text-sm text-muted-foreground mt-1">
            Processing with {processingMethod.toUpperCase()}... {Math.round(uploadProgress)}%
          </p>
        </div>
      )}
    </div>
  );
};
