
import React, { ChangeEvent } from 'react';
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";

interface FileUploadSectionProps {
  onFileUpload: (event: ChangeEvent<HTMLInputElement>) => void;
  isProcessing: boolean;
  acceptedFileTypes: string;
  maxFileSize: number;
}

export const FileUploadSection: React.FC<FileUploadSectionProps> = ({
  onFileUpload,
  isProcessing,
  acceptedFileTypes,
  maxFileSize
}) => {
  const formatFileSize = (bytes: number) => {
    const mb = bytes / (1024 * 1024);
    return `${mb}MB`;
  };

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
      <p className="text-sm text-muted-foreground mt-1">
        Max file size: {formatFileSize(maxFileSize)}
      </p>
      {isProcessing && (
        <div className="mt-2">
          <p className="text-sm text-muted-foreground">
            Processing your credit report...
          </p>
        </div>
      )}
    </div>
  );
};
