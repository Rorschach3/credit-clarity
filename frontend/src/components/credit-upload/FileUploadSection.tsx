
import React, { ChangeEvent, useRef, useState } from 'react';
import { Upload, FileText } from 'lucide-react';
import { Button } from "@/components/ui/button";

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
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);

  const formatFileSize = (bytes: number) => {
    const mb = bytes / (1024 * 1024);
    return `${mb}MB`;
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    if (!isProcessing) setIsDragging(true);
  };

  const handleDragLeave = () => setIsDragging(false);

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (isProcessing) return;
    const file = e.dataTransfer.files[0];
    if (!file) return;
    const dt = new DataTransfer();
    dt.items.add(file);
    const input = fileInputRef.current;
    if (input) {
      // Assign files to the input element and fire a synthetic React change event
      Object.defineProperty(input, 'files', { value: dt.files, configurable: true });
      const syntheticEvent = { target: input } as ChangeEvent<HTMLInputElement>;
      onFileUpload(syntheticEvent);
    }
  };

  const borderColor = isDragging ? '#D4A853' : '#1E2D47';
  const bgColor = isDragging ? 'rgba(212,168,83,0.08)' : 'rgba(26,35,64,0.4)';

  return (
    <div className="space-y-3">
      {/* Drop Zone */}
      <div
        role="button"
        tabIndex={isProcessing ? -1 : 0}
        aria-label="Upload credit report PDF"
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => !isProcessing && fileInputRef.current?.click()}
        onKeyDown={(e) => {
          if ((e.key === 'Enter' || e.key === ' ') && !isProcessing) {
            e.preventDefault();
            fileInputRef.current?.click();
          }
        }}
        className="rounded-xl border-2 border-dashed p-8 flex flex-col items-center gap-3 cursor-pointer transition-all duration-200"
        style={{ borderColor, background: bgColor }}
      >
        <div
          className="w-16 h-16 rounded-full flex items-center justify-center"
          style={{ background: 'rgba(212,168,83,0.15)' }}
        >
          {isProcessing
            ? <div className="animate-spin rounded-full h-8 w-8 border-b-2" style={{ borderColor: '#D4A853' }} />
            : <Upload className="h-8 w-8" style={{ color: '#D4A853' }} />
          }
        </div>

        <div className="text-center">
          <p className="font-semibold text-white text-base">
            {isProcessing ? 'Processing your credit report...' : 'Drag & drop your credit report here'}
          </p>
          <p className="text-sm text-muted-foreground mt-1">
            {isProcessing ? 'This may take a few minutes' : `PDF format · Max ${formatFileSize(maxFileSize)}`}
          </p>
        </div>

        {!isProcessing && (
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <FileText className="h-3 w-3" />
            <span>Supports Experian, Equifax, and TransUnion reports</span>
          </div>
        )}
      </div>

      {/* Hidden input */}
      <input
        ref={fileInputRef}
        id="pdf-upload"
        type="file"
        accept={acceptedFileTypes}
        onChange={onFileUpload}
        disabled={isProcessing}
        className="hidden"
      />

      {/* Gold upload button */}
      <Button
        type="button"
        className="btn-gold w-full rounded-md text-base py-5"
        disabled={isProcessing}
        onClick={() => fileInputRef.current?.click()}
      >
        <Upload className="mr-2 h-4 w-4" />
        {isProcessing ? 'Processing...' : 'Upload Credit Report (PDF)'}
      </Button>
    </div>
  );
};
