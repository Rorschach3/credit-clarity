import React, { useState, useEffect, useCallback } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { toast } from "sonner";
import { useLocation, useNavigate } from "react-router-dom";
import { CreditNavbar } from "@/components/navbar/CreditNavbar";
import { useAuth } from "@/hooks/use-auth";
import { Loader2 } from "lucide-react";
import { supabase } from '@/integrations/supabase/client';
import { usePersistentTradelines } from '@/hooks/usePersistentTradelines';
import { usePersistentProfile } from '@/hooks/usePersistentProfile';
import { TradelinesStatus } from '@/components/ui/tradelines-status';
import { ProfileStatus } from '@/components/ui/profile-status';
import { v4 as uuidv4 } from 'uuid';
import { DocumentUploadSection } from "@/components/disputes/DocumentUploadSection";
import { MailingInstructions } from "@/components/disputes/MailingInstructions";

// Import new components
import { DisputeWizardHeader } from '@/components/dispute-wizard/DisputeWizardHeader';
import { ProfileRequirements } from '@/components/dispute-wizard/ProfileRequirements';
import { ProfileSummary } from '@/components/dispute-wizard/ProfileSummary';
import { TradelineSelection } from '@/components/dispute-wizard/TradelineSelection';
import { DisputeLetterGeneration } from '@/components/dispute-wizard/DisputeLetterGeneration';

// Import lazy-loaded utils
import { 
  generateDisputeLetters, 
  generatePDFPacket,
  type GeneratedDisputeLetter,
  type PacketProgress
} from '@/utils/disputeUtils';
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
  const handleToggleTradelineSelection = useCallback((tradelineId: string) => {
    setSelectedTradelines(prev => {
      const newSelection = new Set(prev);
      if (newSelection.has(tradelineId)) {
        newSelection.delete(tradelineId);
      } else {
        newSelection.add(tradelineId);
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

  const handleGenerateLetters = useCallback(async () => {
    if (!disputeProfile || !isProfileComplete) {
      toast.error("Complete your profile first");
      return;
    }

    if (selectedTradelines.length === 0) {
      toast.error("Select at least one tradeline to dispute");
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

      // Save to database
      await saveDisputePacketRecord(letters, filename);

      setGenerationProgress({ step: 'Complete!', progress: 100, message: 'Dispute packet ready for download' });
      
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

  const saveDisputePacketRecord = async (letters: GeneratedDisputeLetter[], filename: string) => {
    try {
      if (!user?.id) throw new Error('User not authenticated');

      const { error } = await supabase
        .from('dispute_packets')
        .insert({
          id: uuidv4(),
          user_id: user.id,
          filename: filename,
          bureau_count: letters.length,
          tradeline_count: selectedTradelines.length,
          letters_data: letters,
          created_at: new Date().toISOString(),
          status: 'generated'
        });

      if (error) throw error;
    } catch (error) {
      console.error('Error saving dispute packet record:', error);
    }
  };

  const handleDocumentUpload = (documents: UploadedDocument[]) => {
    setUploadedDocuments(documents);
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
      <Card className="max-w-6xl mx-auto space-y-6">
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
              onDocumentsUploaded={handleDocumentUpload}
              documents={uploadedDocuments}
            />
          )}

          {/* Mailing Instructions */}
          {showDocsSection && (
            <MailingInstructions 
              creditBureaus={generatedLetters.map(l => l.creditBureau)}
            />
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default DisputeWizardPage;