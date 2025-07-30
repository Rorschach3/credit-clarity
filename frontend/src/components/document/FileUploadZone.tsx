import { FileText } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useRef, useState } from "react";
import { encryptData, generateCryptoKey, exportCryptoKey } from "@/lib/encryption";
import { createClient } from '@supabase/supabase-js';

interface FileUploadZoneProps {
  file: File | null;
  onFileChange: (file: File | null) => void;
}

const supabase = createClient(
  import.meta.env.VITE_SUPABASE_URL,
  import.meta.env.VITE_SUPABASE_ANON_KEY
);

export function FileUploadZone({ file, onFileChange }: FileUploadZoneProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || !e.target.files[0]) return;

    const selectedFile = e.target.files[0];

    if (selectedFile.type !== 'application/pdf' &&
        !selectedFile.type.includes('image/')) {
      return;
    }

    setUploading(true);
    try {
      // Generate encryption key
      const key = await generateCryptoKey();
      const jwk = await exportCryptoKey(key);

      // Read file as ArrayBuffer
      const arrayBuffer = await selectedFile.arrayBuffer();

      // Encrypt file data
      const encryptedBuffer = await encryptData(key, arrayBuffer);

      // Create Blob from encrypted data
      const encryptedBlob = new Blob([encryptedBuffer], { type: 'application/octet-stream' });

      // Upload encrypted file to Supabase storage
      const filePath = `encrypted-reports/${crypto.randomUUID()}.enc`;
      const { error: uploadError } = await supabase.storage
        .from('encrypted-reports')
        .upload(filePath, encryptedBlob);

      if (uploadError) {
        console.error('Upload error:', uploadError);
        setUploading(false);
        return;
      }

      // Store metadata in credit_reports table
      const user = supabase.auth.getUser ? (await supabase.auth.getUser()).data.user : null;
      const { error: dbError } = await supabase.from('credit_reports').insert({
        user_id: user?.id ?? null,
        encrypted_content: filePath,
        encryption_key_id: JSON.stringify(jwk), // Store key securely in production
        report_date: new Date().toISOString()
      });

      if (dbError) {
        console.error('DB insert error:', dbError);
        setUploading(false);
        return;
      }

      onFileChange(selectedFile);
    } catch (err) {
      console.error('Encryption/upload failed:', err);
    } finally {
      setUploading(false);
    }
  };

  const handleButtonClick = () => {
    fileInputRef.current?.click();
  };

  if (!file) {
    return (
      <div className="flex flex-col items-center justify-center border-2 border-dashed border-gray-300 rounded-lg p-6">
        <FileText className="h-10 w-10 text-gray-400 mb-4" />
        <p className="text-sm text-gray-500">
          Drag and drop your credit report PDF or click to browse
        </p>
        <input
          id="file-upload"
          ref={fileInputRef}
          type="file"
          className="hidden"
          accept=".pdf,.jpg,.jpeg,.png"
          onChange={handleFileChange}
          disabled={uploading}
        />
        <Button
          variant="outline"
          className="cursor-pointer mt-4"
          onClick={handleButtonClick}
          disabled={uploading}
        >
          {uploading ? 'Uploading...' : 'Select File'}
        </Button>
      </div>
    );
  }

  return (
    <div className="w-full text-center">
      <div className="flex items-center justify-center mb-2">
        <FileText className="h-6 w-6 text-primary mr-2" />
        <span className="font-medium">{file.name}</span>
      </div>
      <p className="text-sm text-gray-500 mb-4">
        {Math.round(file.size / 1024)} KB
      </p>

      {file.type === 'application/pdf' && (
        <div className="mb-4">
          <iframe
            src={URL.createObjectURL(file)}
            title="PDF Preview"
            width="100%"
            height="600px"
            className="border border-gray-600 rounded"
          />
        </div>
      )}

      <div className="flex justify-center gap-2">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => onFileChange(null)}
          disabled={uploading}
        >
          Change
        </Button>
      </div>
    </div>
  );
}
