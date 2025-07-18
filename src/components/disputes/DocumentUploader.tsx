
import { useState } from "react";
import { useAuth } from "@/hooks/use-auth";
import { supabase } from "@/integrations/supabase/client";
import { useToast } from "@/hooks/use-toast";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { 
  FileImage, 
  FileText, 
  Loader2, 
  Upload, 
  X, 
  CheckCircle,
  AlertCircle
} from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";

interface DocumentUploaderProps {
  documentType: string;
  title: string;
  description: string;
  acceptedFileTypes?: string;
  onUploadComplete?: () => void;
}

export function DocumentUploader({ 
  documentType, 
  title, 
  description, 
  acceptedFileTypes = "image/*,.pdf", 
  onUploadComplete 
}: DocumentUploaderProps) {
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [existingDocument, setExistingDocument] = useState<any | null>(null);
  const { user } = useAuth();
  const { toast } = useToast();

  const fetchExistingDocument = async () => {
    if (!user) return;
    
    try {
      const { data, error } = await supabase
        .from('user_documents')
        .select('*')
        .eq('user_id', user.id)
        .eq('document_type', documentType)
        .single();
        
      if (error && error.code !== 'PGRST116') { // PGRST116 is "no rows returned"
        console.error("Error fetching existing document:", error);
        return;
      }
      
      if (data) {
        setExistingDocument(data);
      }
    } catch (error) {
      console.error("Error checking for existing document:", error);
    }
  };
  
  // Check for existing document on component mount
  useState(() => {
    fetchExistingDocument();
  });

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      setFile(selectedFile);
      setUploadError(null);
    }
  };

  const uploadDocument = async () => {
    if (!file || !user) {
      toast({
        title: "Error",
        description: !user ? "Please log in to upload documents" : "Please select a file to upload",
        variant: "destructive",
      });
      return;
    }

    setIsUploading(true);
    setUploadProgress(10);
    setUploadError(null);

    try {
      // Create folder path with user ID for better organization
      const filePath = `${user.id}/${documentType}/${Date.now()}_${file.name}`;
      
      // Upload to Supabase Storage
      const { error: storageError } = await supabase.storage
        .from('dispute_documents')
        .upload(filePath, file, {
          cacheControl: '3600',
          upsert: existingDocument ? true : false,
        });

      if (storageError) throw storageError;
      
      setUploadProgress(60);
      
      // Record in database
      const documentRecord = {
        user_id: user.id,
        document_type: documentType,
        file_path: filePath,
        file_name: file.name,
        content_type: file.type,
      };
      
      let dbOperation;
      
      if (existingDocument) {
        // Update existing record
        dbOperation = supabase
          .from('user_documents')
          .update(documentRecord)
          .eq('id', existingDocument.id);
      } else {
        // Create new record
        dbOperation = supabase
          .from('user_documents')
          .insert([documentRecord]);
      }
      
      const { error: dbError } = await dbOperation;
      
      if (dbError) throw dbError;
      
      setUploadProgress(100);
      
      toast({
        title: "Upload Successful",
        description: `${title} has been uploaded successfully.`,
      });
      
      // Refresh the document data
      await fetchExistingDocument();
      
      if (onUploadComplete) {
        onUploadComplete();
      }
    } catch (error) {
      console.error("Error uploading document:", error);
      setUploadError("There was an error uploading your document. Please try again.");
      toast({
        title: "Upload Failed",
        description: "There was an error uploading your document. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsUploading(false);
      setFile(null);
    }
  };

  const handleRemoveDocument = async () => {
    if (!existingDocument || !user) return;
    
    try {
      // Delete file from storage
      const { error: storageError } = await supabase.storage
        .from('dispute_documents')
        .remove([existingDocument.file_path]);
        
      if (storageError) throw storageError;
      
      // Delete record from database
      const { error: dbError } = await supabase
        .from('user_documents')
        .delete()
        .eq('id', existingDocument.id);
        
      if (dbError) throw dbError;
      
      toast({
        title: "Document Removed",
        description: `${title} has been removed successfully.`,
      });
      
      setExistingDocument(null);
    } catch (error) {
      console.error("Error removing document:", error);
      toast({
        title: "Error",
        description: "There was an error removing your document. Please try again.",
        variant: "destructive",
      });
    }
  };

  const displayFileType = (contentType: string | null) => {
    if (!contentType) return <FileText className="h-8 w-8" />;
    
    if (contentType.startsWith('image/')) {
      return <FileImage className="h-8 w-8" />;
    } else {
      return <FileText className="h-8 w-8" />;
    }
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent>
        {existingDocument ? (
          <div className="flex flex-col items-center justify-center p-4 border rounded-lg bg-gray-50">
            <div className="flex items-center mb-2">
              <CheckCircle className="h-5 w-5 text-green-500 mr-2" />
              <span className="font-medium">Document Uploaded</span>
              <Badge variant="outline" className="ml-2">
                {existingDocument.verified ? "Verified" : "Pending Verification"}
              </Badge>
            </div>
            <div className="flex items-center justify-center mt-2">
              {displayFileType(existingDocument.content_type)}
              <span className="ml-2 text-sm text-gray-600">{existingDocument.file_name}</span>
            </div>
            <div className="flex justify-center mt-4">
              <Button variant="outline" size="sm" onClick={handleRemoveDocument}>
                <X className="h-4 w-4 mr-1" />
                Remove
              </Button>
            </div>
          </div>
        ) : (
          <>
            {uploadError && (
              <Alert variant="destructive" className="mb-4">
                <AlertCircle className="h-4 w-4" />
                <AlertTitle>Error</AlertTitle>
                <AlertDescription>{uploadError}</AlertDescription>
              </Alert>
            )}
            
            <div className="flex flex-col items-center border-2 border-dashed rounded-md p-6 mb-4">
              {file ? (
                <div className="flex flex-col items-center">
                  {file.type.startsWith('image/') ? (
                    <FileImage className="h-12 w-12 text-blue-500" />
                  ) : (
                    <FileText className="h-12 w-12 text-blue-500" />
                  )}
                  <p className="mt-2 text-sm font-medium">{file.name}</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    {(file.size / 1024).toFixed(2)} KB
                  </p>
                </div>
              ) : (
                <div className="flex flex-col items-center">
                  <Upload className="h-10 w-10 text-gray-400 mb-2" />
                  <p className="text-sm text-center text-muted-foreground">
                    Drag and drop your {title.toLowerCase()} here, or click to browse
                  </p>
                </div>
              )}
            </div>
            
            <div>
              <input
                id={`file-upload-${documentType}`}
                type="file"
                accept={acceptedFileTypes}
                onChange={handleFileChange}
                className="hidden"
                disabled={isUploading}
              />
              
              <div className="flex justify-center space-x-4">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => document.getElementById(`file-upload-${documentType}`)?.click()}
                  disabled={isUploading || !!file}
                >
                  Browse Files
                </Button>
                
                <Button
                  type="button"
                  disabled={!file || isUploading}
                  onClick={uploadDocument}
                >
                  {isUploading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Uploading...
                    </>
                  ) : (
                    <>
                      <Upload className="mr-2 h-4 w-4" />
                      Upload Document
                    </>
                  )}
                </Button>
              </div>
              
              {isUploading && (
                <div className="mt-4">
                  <p className="text-sm mb-1">Uploading: {uploadProgress}%</p>
                  <Progress value={uploadProgress} className="h-2" />
                </div>
              )}
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}
