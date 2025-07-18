
import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { DocumentUploader } from "./DocumentUploader";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { AlertCircle, Info, ArrowRight } from "lucide-react";
import { supabase } from "@/integrations/supabase/client";
import { useAuth } from "@/hooks/use-auth";

interface UserDocumentsSectionProps {
  onComplete?: () => void;
}

export function UserDocumentsSection({ onComplete }: UserDocumentsSectionProps) {
  const [documentStatus, setDocumentStatus] = useState({
    photoId: false,
    ssnCard: false,
    utilityBill: false
  });
  const { user } = useAuth();

  useEffect(() => {
    const checkDocumentStatus = async () => {
      if (!user) return;

      try {
        const { data, error } = await supabase
          .from('user_documents')
          .select('document_type')
          .eq('user_id', user.id);

        if (error) {
          console.error("Error checking document status:", error);
          return;
        }

        // Update document status based on what's available
        const updatedStatus = {
          photoId: false,
          ssnCard: false,
          utilityBill: false
        };

        if (data) {
          data.forEach(doc => {
            if (doc.document_type === 'photo_id') updatedStatus.photoId = true;
            if (doc.document_type === 'ssn_card') updatedStatus.ssnCard = true;
            if (doc.document_type === 'utility_bill') updatedStatus.utilityBill = true;
          });
        }

        setDocumentStatus(updatedStatus);
      } catch (error) {
        console.error("Error in checking document status:", error);
      }
    };

    checkDocumentStatus();
  }, [user]);

  // Check if all required documents are uploaded
  const allDocumentsUploaded = documentStatus.photoId && documentStatus.ssnCard && documentStatus.utilityBill;
  
  // Handler for when any document is uploaded
  const handleDocumentUpload = () => {
    // Refresh document status
    if (user) {
      supabase
        .from('user_documents')
        .select('document_type')
        .eq('user_id', user.id)
        .then(({ data, error }) => {
          if (error) {
            console.error("Error checking document status:", error);
            return;
          }

          // Update document status based on what's available
          const updatedStatus = {
            photoId: false,
            ssnCard: false,
            utilityBill: false
          };

          if (data) {
            data.forEach(doc => {
              if (doc.document_type === 'photo_id') updatedStatus.photoId = true;
              if (doc.document_type === 'ssn_card') updatedStatus.ssnCard = true;
              if (doc.document_type === 'utility_bill') updatedStatus.utilityBill = true;
            });
          }

          setDocumentStatus(updatedStatus);
          
          // If all documents are uploaded, call onComplete
          if (updatedStatus.photoId && updatedStatus.ssnCard && updatedStatus.utilityBill && onComplete) {
            onComplete();
          }
        });
    }
  };

  const handleSkipDocuments = () => {
    if (onComplete) onComplete();
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>Required Identity Documents</CardTitle>
        <CardDescription>
          Credit bureaus require these documents to process your dispute. 
          All documents must be clear, legible, and unedited.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <Alert variant="default" className="bg-blue-50 text-blue-700 border-blue-200">
          <Info className="h-4 w-4" />
          <AlertTitle>Why are these documents needed?</AlertTitle>
          <AlertDescription>
            Credit bureaus require these documents to verify your identity before processing any 
            dispute. Without them, bureaus will typically reject your dispute request.
          </AlertDescription>
        </Alert>

        {allDocumentsUploaded && (
          <Alert variant="default" className="bg-green-50 text-green-700 border-green-200">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>All Required Documents Uploaded</AlertTitle>
            <AlertDescription className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-2">
              <span>You've successfully uploaded all required identity documents.</span>
              <Button 
                onClick={handleSkipDocuments}
                className="bg-green-600 hover:bg-green-700"
              >
                Continue to Letter Generation <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </AlertDescription>
          </Alert>
        )}

        <div className="flex flex-col gap-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <DocumentUploader 
              documentType="photo_id"
              title="Government-Issued Photo ID"
              description="Upload a clear photo of your driver's license, passport, or state ID"
              acceptedFileTypes="image/jpeg,image/png,image/jpg,.pdf"
              onUploadComplete={handleDocumentUpload}
            />
            
            <DocumentUploader 
              documentType="ssn_card"
              title="Social Security Card"
              description="Upload a clear photo of your Social Security card"
              acceptedFileTypes="image/jpeg,image/png,image/jpg,.pdf"
              onUploadComplete={handleDocumentUpload}
            />
          </div>

          <DocumentUploader 
            documentType="utility_bill"
            title="Utility Bill or Proof of Address"
            description="Upload a recent utility bill, bank statement, or other document showing your current address"
            acceptedFileTypes="image/jpeg,image/png,image/jpg,.pdf"
            onUploadComplete={handleDocumentUpload}
          />
        </div>

        <div className="mt-6 pt-4 border-t border-gray-200">
          <Button 
            variant="outline" 
            onClick={handleSkipDocuments}
            className="w-full"
          >
            Skip Document Upload & Continue <ArrowRight className="ml-2 h-4 w-4" />
          </Button>
          <p className="text-sm text-muted-foreground mt-2 text-center">
            Note: Skipping may reduce your chances of a successful dispute with credit bureaus.
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
