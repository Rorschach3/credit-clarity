
import React, { ChangeEvent } from 'react';
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Progress } from "@/components/ui/progress";

interface FileUploadSectionProps {
  onFileUpload: (event: ChangeEvent<HTMLInputElement>) => void;
  isProcessing: boolean;
  acceptedFileTypes?: string;
  maxFileSize?: number;
}

export const FileUploadSection: React.FC<FileUploadSectionProps> = ({
  onFileUpload,
  isProcessing,
  acceptedFileTypes = ".pdf",
  maxFileSize = 10 * 1024 * 1024 // 10MB default
}) => {
  return (
    <div>
      <Label htmlFor="pdf-upload">Upload Credit Report (PDF)</Label>
      <Input
        id="pdf-upload"
        type="file"
        accept={acceptedFileTypes}
        onChange={onFileUpload}
        disabled={isProcessing}
      />
      {isProcessing && (
        <div className="mt-2">
          <p className="text-sm text-muted-foreground mt-1">
            Processing file...
          </p>
        </div>
      )}
    </div>
  );
};
