import React, { useState, useEffect, useCallback } from "react";
import { toast } from "sonner";
import { useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "@/hooks/use-auth";
import { useWorkflowState } from "@/hooks/useWorkflowState";
import { supabase } from '@/integrations/supabase/client';
import { usePersistentTradelines } from '@/hooks/usePersistentTradelines';
import { usePersistentProfile } from '@/hooks/usePersistentProfile';
import { Loader2 } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";

// Import components (these need to be created or imported from the correct paths)
import { CreditNavbar } from "@/components/navbar/CreditNavbar";
import { WorkflowNavigation } from "@/components/workflow/WorkflowNavigation";
import { DisputeWizardHeader } from "@/components/dispute-wizard/DisputeWizardHeader";
import { ProfileRequirements } from "@/components/dispute-wizard/ProfileRequirements";
import { ProfileStatus } from "@/components/profile-status";
import { TradelinesStatus } from "@/components/ui/tradelines-status";
import { ProfileSummary } from "@/components/dispute-wizard/ProfileSummary";
import { TradelineSelection } from "@/components/dispute-wizard/TradelineSelection";
import { DisputeLetterGeneration } from "@/components/dispute-wizard/DisputeLetterGeneration";
import { DocumentUploadSection } from "@/components/disputes/DocumentUploadSection";
import { PacketGenerationSection } from "@/components/disputes/PacketGenerationSection";
import { MailingInstructions } from "@/components/disputes/MailingInstructions";

// Import lazy-loaded utils
import { 
  generateDisputeLetters, 
  generatePDFPacket,
  generateCompletePacket,
  type GeneratedDisputeLetter,
  type PacketProgress
} from '@/utils/disputeUtils';
import { 
  fetchUserDocuments,
  downloadDocumentBlobs,
  hasRequiredDocuments,
  getMissingDocuments,
  type DocumentBlob
} from '@/utils/documentPacketUtils';
import { type ParsedTradeline } from '@/utils/tradelineParser';

interface UploadedDocument {
  id: string;
  name: string;
  type: string;
  file: File;
  preview?: string;
}

const DisputeWizardPage = () => {
  const { user } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  
  // State management
  const [showDocsSection, setShowDocsSection] = useState(false);
  const [documentsCompleted, setDocumentsCompleted] = useState(false);
  const [showPacketGeneration, setShowPacketGeneration] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [generationProgress, setGenerationProgress] = useState<PacketProgress>({
    step: '',
    progress: 0,
    message: ''
  });
  
  // Use persistent hooks
  const {
    disputeProfile,
    loading: profileLoading,
    error: profileError,
    refreshProfile,
    isProfileComplete,
    missingFields
  } = usePersistentProfile();
  
  const {
    tradelines: persistentTradelines,
    loading: tradelinesLoading,
    error: tradelinesError,
    getNegativeTradelines: getPersistentNegativeTradelines,
    refreshTradelines
  } = usePersistentTradelines();

  // Use workflow state
  const { workflowState, refreshWorkflowState } = useWorkflowState();

  // Component state
  const [negativeTradelines, setNegativeTradelines] = useState<ParsedTradeline[]>([]);
  const [selectedTradelines, setSelectedTradelines] = useState<string[]>([]);
  const [generatedLetters, setGeneratedLetters] = useState<GeneratedDisputeLetter[]>([]);
  const [uploadedDocuments, setUploadedDocuments] = useState<UploadedDocument[]>([]);
  const [generatedPDF, setGeneratedPDF] = useState<Blob | null>(null);
  const [pdfFilename, setPdfFilename] = useState<string>('');
  const [editingLetter, setEditingLetter] = useState<string | null>(null);
  const [editedContent, setEditedContent] = useState<string>('');

  // Load user data when component mounts
  useEffect(() => {
    if (user?.id) {
      setIsLoading(true);
      const timer = setTimeout(() => {
        setIsLoading(false);
      }, 100);
      return () => clearTimeout(timer);
    } else {
      setIsLoading(false);
    }
  }, [user?.id]);

  // Sync persistent tradelines with local negative tradelines
  useEffect(() => {
    if (persistentTradelines.length > 0) {
      const negative = getPersistentNegativeTradelines();
      console.log('[DEBUG] 🔴 Syncing negative tradelines from persistent storage:', negative.length);
      
      setNegativeTradelines(negative);
      setSelectedTradelines(negative.map(t => t.id));
      
      if (negative.length > 0) {
        toast.success(`Found ${negative.length} negative tradeline(s) for dispute`, {
          description: "Ready to generate dispute letters"
        });
      }
    }
  }, [persistentTradelines, getPersistentNegativeTradelines]);

  // Handle initial route state
  useEffect(() => {
    if (location.state?.initialSelectedTradelines) {
      const initialTradelines = location.state.initialSelectedTradelines;
      setNegativeTradelines(initialTradelines);
      setSelectedTradelines(initialTradelines.map((t: ParsedTradeline) => t.id));
      
      toast.info(`Loaded ${initialTradelines.length} tradeline(s) from tradelines page`, {
        description: "Ready to generate dispute letters"
      });
    }
  }, [location.state]);

  // Computed values
  const isReadyToGenerate = disputeProfile && isProfileComplete && selectedTradelines.length > 0 && !isLoading && !profileLoading;

  // Event handlers
  const handleToggleTradelineSelection = useCallback((userId: string) => {
    setSelectedTradelines(prev => {
      const newSelection = new Set(prev);
      if (newSelection.has(userId)) {
        newSelection.delete(userId);
      } else {
        newSelection.add(userId);
      }
      return Array.from(newSelection);
    });
  }, []);

  const handleSelectAllTradelines = useCallback(() => {
    setSelectedTradelines(negativeTradelines.map(t => t.id));
  }, [negativeTradelines]);

  const handleDeselectAllTradelines = useCallback(() => {
    setSelectedTradelines([]);
  }, []);

  const saveDisputePacketRecord = async (
    userId: string,
    letters: GeneratedDisputeLetter[],
    filename: string
  ) => {
    try {
      // Start with base schema columns that definitely exist
      const disputePacketData: any = {
        user_id: userId,
        packet_status: 'generated',
      };

      // Try to add optional columns that may exist after migration
      try {
        // Test if we can safely add these fields by doing a quick schema check
        const { error: testError } = await supabase
          .from('dispute_packets')
          .select('filename, bureau_count, tradeline_count, letters_data')
          .limit(0);

        if (!testError) {
          // Schema supports these columns, add them
          disputePacketData.filename = filename;
          disputePacketData.bureau_count = letters.length;
          disputePacketData.tradeline_count = letters.reduce((sum, l) => sum + l.tradelines.length, 0);
          disputePacketData.letters_data = letters;
        }
      } catch (schemaError) {
        console.log('Extended schema not available yet, using base schema');
      }

      // Always include base columns that exist in the original schema
      disputePacketData.document_urls = [];
      disputePacketData.dispute_letter_url = null;

      const { error } = await supabase
        .from('dispute_packets')
        .insert(disputePacketData);

      if (error) {
        console.error('Supabase error details:', error);
        throw error;
      }
      
      console.log('Successfully saved dispute packet record');
    } catch (error) {
      console.error('Error saving dispute packet record:', error);
      // Don't throw the error to prevent breaking the UX
      // The letters are still generated successfully
    }
  };

  // Fixed: Added missing handleGenerateLetters function
  const handleGenerateLetters = useCallback(async () => {
    if (!disputeProfile || !isProfileComplete || selectedTradelines.length === 0) {
      toast.error("Please ensure your profile is complete and select tradelines to dispute");
      return;
    }

    setIsGenerating(true);
    setGenerationProgress({ step: 'Starting...', progress: 0, message: 'Initializing dispute letter generation' });

    try {
      // Generate letters
      const letters = await generateDisputeLetters(
        selectedTradelines,
        negativeTradelines,
        disputeProfile,
        setGenerationProgress
      );

      // Generate PDF
      const pdfBlob = await generatePDFPacket(letters, setGenerationProgress);
      const filename = `dispute-packet-${new Date().toISOString().split('T')[0]}.pdf`;

      setGeneratedLetters(letters);
      setGeneratedPDF(pdfBlob);
      setPdfFilename(filename);
      setShowDocsSection(true);

      setGenerationProgress({ step: 'Letters Generated!', progress: 100, message: 'Now upload supporting documents' });
      
      toast.success("Dispute letters generated successfully!", {
        description: `Created ${letters.length} letter(s) for ${selectedTradelines.length} tradeline(s)`
      });

    } catch (error) {
      console.error('Error generating dispute letters:', error);
      toast.error("Failed to generate dispute letters", {
        description: "Please try again or contact support"
      });
    } finally {
      setIsGenerating(false);
    }
  }, [disputeProfile, isProfileComplete, selectedTradelines, negativeTradelines]);

  const handleDocumentUpload = (documents: UploadedDocument[]) => {
    setUploadedDocuments(documents);
  };

  const handleDocumentsComplete = () => {
    setDocumentsCompleted(true);
    setShowDocsSection(false);
    setShowPacketGeneration(true);
    toast.success("Documents uploaded successfully!", {
      description: "Ready to generate final dispute packet"
    });
  };

  const handleSkipDocuments = () => {
    setDocumentsCompleted(true);
    setShowDocsSection(false);
    setShowPacketGeneration(true);
    toast.info("Documents skipped", {
      description: "Proceeding to generate dispute packet"
    });
  };

  const handleDownloadPDF = () => {
    if (!generatedPDF) return;
    
    const url = URL.createObjectURL(generatedPDF);
    const a = document.createElement('a');
    a.href = url;
    a.download = pdfFilename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    toast.success("PDF downloaded successfully!", {
      description: "Print, sign, and mail with certified mail"
    });
  };

  const handleEditLetter = (letterId: string, content: string) => {
    setEditingLetter(letterId);
    setEditedContent(content);
  };

  const handleSaveEdit = () => {
    if (!editingLetter) return;
    
    setGeneratedLetters(prev => prev.map(letter => 
      letter.id === editingLetter 
        ? { ...letter, letterContent: editedContent, isEdited: true }
        : letter
    ));
    
    setEditingLetter(null);
    setEditedContent('');
    setGeneratedPDF(null); // Reset PDF since content changed
    
    toast.success("Letter updated successfully", {
      description: "Regenerate PDF to include your changes"
    });
  };

  const handleCancelEdit = () => {
    setEditingLetter(null);
    setEditedContent('');
  };

  const handlePrepareDisputePacket = async () => {
    if (!user?.id || !generatedLetters.length) {
      toast.error("No dispute letters ready");
      return;
    }

    try {
      setIsGenerating(true);
      setGenerationProgress({ 
        step: 'Fetching documents...', 
        progress: 0, 
        message: 'Checking for uploaded documents' 
      });

      // Fetch user documents
      const userDocuments = await fetchUserDocuments(user.id);
      
      setGenerationProgress({ 
        step: 'Validating documents...', 
        progress: 10, 
        message: 'Checking required documents' 
      });

      // Check if we have documents to include
      let documentBlobs: DocumentBlob[] = [];
      
      if (userDocuments.length > 0) {
        // Check for missing documents
        const missingDocs = getMissingDocuments(userDocuments);
        if (missingDocs.length > 0) {
          toast.info(`Missing documents: ${missingDocs.join(', ')}`, {
            description: "Proceeding with available documents"
          });
        }

        // Download document blobs
        documentBlobs = await downloadDocumentBlobs(userDocuments, setGenerationProgress);
        
        if (documentBlobs.length === 0) {
          toast.warning("No documents could be downloaded", {
            description: "Creating packet with dispute letters only"
          });
        }
      } else {
        toast.info("No documents uploaded", {
          description: "Creating packet with dispute letters only"
        });
      }

      // Generate complete packet
      const completePacket = await generateCompletePacket(
        generatedLetters, 
        documentBlobs, 
        setGenerationProgress
      );

      // Update the generated PDF state
      setGeneratedPDF(completePacket);
      
      const fileName = `complete-dispute-packet-${Date.now()}.pdf`;
      setPdfFilename(fileName);

      setGenerationProgress({ 
        step: 'Uploading packet...', 
        progress: 80, 
        message: 'Uploading to secure storage' 
      });

      // Upload complete packet to storage
      const filePath = `${user.id}/${fileName}`;
      const { error: uploadError } = await supabase.storage
        .from('dispute_packets')
        .upload(filePath, completePacket, {
          contentType: 'application/pdf',
          upsert: false
        });

      if (uploadError) throw uploadError;

      setGenerationProgress({ 
        step: 'Saving to database...', 
        progress: 90, 
        message: 'Saving packet information' 
      });

      // Save to database with updated info
      await saveDisputePacketRecord(user.id, generatedLetters, fileName);

      // Update the dispute packet record with the storage URL
      const { error: updateError } = await supabase
        .from('dispute_packets')
        .update({
          dispute_letter_url: filePath,
          packet_status: 'ready',
          updated_at: new Date().toISOString()
        })
        .eq('user_id', user.id)
        .eq('filename', fileName);

      if (updateError) throw updateError;

      setGenerationProgress({ 
        step: 'Complete!', 
        progress: 100, 
        message: 'Complete dispute packet ready for download' 
      });

      // Refresh workflow state to mark as completed
      refreshWorkflowState();

      const documentsIncluded = documentBlobs.length;
      toast.success("Complete dispute packet prepared successfully!", {
        description: `Includes ${generatedLetters.length} letter(s) and ${documentsIncluded} document(s)`
      });

      // Close the packet generation section
      setShowPacketGeneration(false);

    } catch (error) {
      console.error('Error preparing dispute packet:', error);
      toast.error("Failed to prepare dispute packet", {
        description: "Please try again or contact support"
      });
    } finally {
      setIsGenerating(false);
    }
  };

  // Loading state
  if (isLoading || profileLoading) {
    return (
      <div className="min-h-screen bg-background text-foreground py-10 px-4 md:px-10">
        <CreditNavbar />
        <Card className="max-w-6xl mx-auto">
          <CardContent className="p-8">
            <div className="flex items-center justify-center space-x-2">
              <Loader2 className="h-6 w-6 animate-spin" />
              <span>Loading your profile and credit data...</span>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background text-foreground py-10 px-4 md:px-10">
      <CreditNavbar />
      
      <div className="max-w-6xl mx-auto space-y-6">
        
        {/* Workflow Navigation */}
        <WorkflowNavigation
          currentStep="dispute"
          completionData={{
            hasUploadedReports: workflowState.hasUploadedReports,
            hasSelectedTradelines: workflowState.hasSelectedTradelines,
            hasGeneratedLetter: workflowState.hasGeneratedPacket
          }}
          canProceed={false} // This is the final step
        />
        
        <Card className="space-y-6">
          <DisputeWizardHeader />
          
          <CardContent className="space-y-6">
            
            {/* Requirements Check */}
            <ProfileRequirements
              disputeProfile={disputeProfile}
              isProfileComplete={isProfileComplete}
              missingFields={missingFields}
            />

            {/* Status Components */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <ProfileStatus
                loading={profileLoading}
                error={profileError}
                isComplete={isProfileComplete}
                missingFields={missingFields}
                onRefresh={refreshProfile}
                onEdit={() => navigate('/profile')}
              />
              <TradelinesStatus
                loading={tradelinesLoading}
                error={tradelinesError}
                tradelinesCount={persistentTradelines.length}
                onRefresh={refreshTradelines}
              />
            </div>

            {/* Profile Summary */}
            <ProfileSummary
              disputeProfile={disputeProfile}
              isProfileComplete={isProfileComplete}
            />

            {/* Tradeline Selection */}
            <TradelineSelection
              negativeTradelines={negativeTradelines}
              selectedTradelines={selectedTradelines}
              onToggleSelection={handleToggleTradelineSelection}
              onSelectAll={handleSelectAllTradelines}
              onDeselectAll={handleDeselectAllTradelines}
            />

            {/* Dispute Letter Generation */}
            <DisputeLetterGeneration
              isGenerating={isGenerating}
              generationProgress={generationProgress}
              generatedLetters={generatedLetters}
              editingLetter={editingLetter}
              editedContent={editedContent}
              isReadyToGenerate={isReadyToGenerate}
              onGenerate={handleGenerateLetters}
              onEditLetter={handleEditLetter}
              onSaveEdit={handleSaveEdit}
              onCancelEdit={handleCancelEdit}
              onEditContentChange={setEditedContent}
              onDownloadPDF={handleDownloadPDF}
              generatedPDF={generatedPDF}
            />

            {/* Document Upload Section */}
            {showDocsSection && (
              <DocumentUploadSection 
                onClose={() => setShowDocsSection(false)}
                onComplete={handleDocumentsComplete}
                onSkip={handleSkipDocuments}
              />
            )}

            {/* Packet Generation Section */}
            {showPacketGeneration && (
              <PacketGenerationSection
                isGenerating={isGenerating}
                generationProgress={generationProgress}
                generatedPDF={generatedPDF}
                documentsCompleted={documentsCompleted}
                onPreparePacket={handlePrepareDisputePacket}
                onDownloadPDF={handleDownloadPDF}
                onClose={() => setShowPacketGeneration(false)}
              />
            )}

            {/* Mailing Instructions */}
            {showPacketGeneration && generationProgress.progress === 100 && (
              <MailingInstructions 
                creditBureaus={generatedLetters.map(l => l.creditBureau)}
              />
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default DisputeWizardPage;