import React, { useState, useEffect, useCallback } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { toast } from "sonner";
import { useLocation, useNavigate } from "react-router-dom";
import { CreditNavbar } from "@/components/navbar/CreditNavbar";
import { useAuth } from "@/hooks/use-auth";
import { Loader2 } from "lucide-react";
import { supabase } from '@/integrations/supabase/client';
import { usePersistentTradelines } from '@/hooks/usePersistentTradelines';
import { usePersistentProfile, clearProfileCache } from '@/hooks/usePersistentProfile';
import { TradelinesStatus } from '@/components/ui/tradelines-status';
import { ProfileStatus } from '@/components/ui/profile-status';
import { v4 as uuidv4 } from 'uuid';
import { DocumentUploadSection } from "@/components/disputes/DocumentUploadSection";
import { MailingInstructions } from "@/components/disputes/MailingInstructions";
import ChatbotWidget from "@/components/ChatbotWidget";

// Import new components
import { DisputeWizardHeader } from '@/components/dispute-wizard/DisputeWizardHeader';
import { ProfileRequirements } from '@/components/dispute-wizard/ProfileRequirements';
import { ProfileSummary } from '@/components/dispute-wizard/ProfileSummary';
import { TradelineSelection } from '@/components/dispute-wizard/TradelineSelection';
import { DisputeLetterGeneration } from '@/components/dispute-wizard/DisputeLetterGeneration';
import { DuplicateDisputeModal } from '@/components/dispute-wizard/DuplicateDisputeModal';
import { CROADisclosureModal } from '@/components/croa/CROADisclosureModal';

// Import types only (no code execution)
import { type ParsedTradeline } from '@/utils/tradelineParser';
import type { GeneratedDisputeLetter, PacketProgress } from '@/utils/disputeUtils';

// Lazy load PDF utilities only when needed (dynamic import)
const loadPDFUtils = async () => {
  const [disputeUtils, docPacketUtils] = await Promise.all([
    import('@/utils/disputeUtils'),
    import('@/utils/documentPacketUtils'),
  ]);

  return {
    generateDisputeLetters: disputeUtils.generateDisputeLetters,
    generatePDFPacket: disputeUtils.generatePDFPacket,
    generateCompletePacket: disputeUtils.generateCompletePacket,
    saveLettersToDisputesTable: disputeUtils.saveLettersToDisputesTable,
    checkDuplicateDispute: disputeUtils.checkDuplicateDispute,
    fetchUserDocuments: docPacketUtils.fetchUserDocuments,
    downloadDocumentBlobs: docPacketUtils.downloadDocumentBlobs,
  };
};


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
    missingFields,
    croaAccepted
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
  const [generatedPDF, setGeneratedPDF] = useState<Blob | null>(null);
  const [pdfFilename, setPdfFilename] = useState<string>('');
  const [editingLetter, setEditingLetter] = useState<string | null>(null);
  const [editedContent, setEditedContent] = useState<string>('');
  const [duplicateModalOpen, setDuplicateModalOpen] = useState(false);
  const [duplicateInfo, setDuplicateInfo] = useState<Array<{ disputeId: string; creditorName: string; bureau: string }>>([]);

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
  const isReadyToGenerate = !!(disputeProfile && isProfileComplete && selectedTradelines.length > 0 && !isLoading && !profileLoading);

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

  const proceedWithGeneration = useCallback(async () => {
    setIsGenerating(true);
    setGenerationProgress({ step: 'Starting...', progress: 0, message: 'Initializing dispute letter generation' });

    try {
      // Dynamically load PDF utilities (lazy loading)
      const pdfUtils = await loadPDFUtils();

      // Generate letters
      const letters = await pdfUtils.generateDisputeLetters(
        selectedTradelines,
        negativeTradelines,
        disputeProfile,
        setGenerationProgress
      );

      // Generate PDF
      const pdfBlob = await pdfUtils.generatePDFPacket(letters, setGenerationProgress);
      const filename = `dispute-packet-${new Date().toISOString().split('T')[0]}.pdf`;

      setGeneratedLetters(letters);
      setGeneratedPDF(pdfBlob);
      setPdfFilename(filename);
      setShowDocsSection(true);

      // Save packet summary to dispute_packets table
      await saveDisputePacketRecord(letters, filename);

      // Also persist individual letter records to disputes table for history tracking
      try {
        const activeTradelines = negativeTradelines.filter(t => selectedTradelines.includes(t.id));
        await pdfUtils.saveLettersToDisputesTable(letters, user!.id, activeTradelines);
      } catch (historyErr) {
        console.warn('[DisputeWizard] Non-critical: failed to save letters to dispute history:', historyErr);
      }

      setGenerationProgress({ step: 'Complete!', progress: 100, message: 'Dispute packet ready for download' });

      toast.success("Dispute letters generated successfully!", {
        description: `Created ${letters.length} letter(s) for ${selectedTradelines.length} tradeline(s)`
      });

      // Send confirmation email (non-blocking)
      if (user?.email) {
        supabase.functions.invoke('send-email', {
          body: {
            type: 'dispute_packet_ready',
            to: user.email,
            userName: disputeProfile?.firstName ?? 'there',
            data: {
              bureauCount: letters.length,
              itemCount: selectedTradelines.length,
              appUrl: window.location.origin,
            },
          },
        }).catch(() => {}); // fire-and-forget
      }

    } catch (error) {
      console.error('Error generating dispute letters:', error);
      toast.error("Failed to generate dispute letters", {
        description: "Please try again or contact support"
      });
    } finally {
      setIsGenerating(false);
    }
  }, [disputeProfile, selectedTradelines, negativeTradelines, user]);

  const handleGenerateLetters = useCallback(async () => {
    if (!disputeProfile || !isProfileComplete) {
      toast.error("Complete your profile first");
      return;
    }

    if (selectedTradelines.length === 0) {
      toast.error("Select at least one tradeline to dispute");
      return;
    }

    // Check for duplicates before generating
    if (user?.id) {
      try {
        const pdfUtils = await loadPDFUtils();
        const activeTradelines = negativeTradelines.filter(t => selectedTradelines.includes(t.id));
        const BUREAUS = ['Equifax', 'Experian', 'TransUnion'];

        const duplicates: Array<{ disputeId: string; creditorName: string; bureau: string }> = [];
        for (const tradeline of activeTradelines) {
          const bureauList = tradeline.credit_bureau ? [tradeline.credit_bureau] : BUREAUS;
          for (const bureau of bureauList) {
            const existingId = await pdfUtils.checkDuplicateDispute(
              user.id,
              tradeline.creditor_name ?? '',
              tradeline.account_number
                ? tradeline.account_number.length > 4
                  ? `****${tradeline.account_number.slice(-4)}`
                  : tradeline.account_number
                : '',
              bureau
            );
            if (existingId) {
              duplicates.push({ disputeId: existingId, creditorName: tradeline.creditor_name ?? 'Unknown', bureau });
            }
          }
        }

        if (duplicates.length > 0) {
          setDuplicateInfo(duplicates);
          setDuplicateModalOpen(true);
          return;
        }
      } catch (dupErr) {
        console.warn('[DisputeWizard] Duplicate check failed, proceeding anyway:', dupErr);
      }
    }

    await proceedWithGeneration();
  }, [disputeProfile, isProfileComplete, selectedTradelines, negativeTradelines, user, proceedWithGeneration]);

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


  const triggerDownload = (blob: Blob, filename: string) => {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleDownloadPDF = () => {
    if (!generatedPDF) return;
    triggerDownload(generatedPDF, pdfFilename);
    toast.success("PDF downloaded successfully!", {
      description: "Print, sign, and mail with certified mail"
    });
  };

  const handlePreparePacket = async () => {
    if (!user?.id || generatedLetters.length === 0) return;

    setIsGenerating(true);
    setGenerationProgress({ step: 'Fetching documents...', progress: 10, message: 'Loading your uploaded supporting documents' });

    try {
      const pdfUtils = await loadPDFUtils();

      // Fetch any uploaded supporting documents
      const userDocs = await pdfUtils.fetchUserDocuments(user.id);

      if (userDocs.length === 0) {
        // No documents uploaded — just download the letter-only PDF
        handleDownloadPDF();
        setIsGenerating(false);
        return;
      }

      setGenerationProgress({ step: 'Downloading documents...', progress: 30, message: `Found ${userDocs.length} supporting document(s)` });

      const docBlobs = await pdfUtils.downloadDocumentBlobs(userDocs, setGenerationProgress);

      setGenerationProgress({ step: 'Building packet...', progress: 60, message: 'Merging letters and supporting documents' });

      const completeBlob = await pdfUtils.generateCompletePacket(generatedLetters, docBlobs, setGenerationProgress);
      const filename = `dispute-packet-complete-${new Date().toISOString().split('T')[0]}.pdf`;

      triggerDownload(completeBlob, filename);
      toast.success('Complete dispute packet downloaded!', {
        description: `Includes ${generatedLetters.length} letter(s) + ${docBlobs.length} supporting document(s)`
      });
    } catch (err) {
      console.error('[DisputeWizard] Packet preparation error:', err);
      // Fall back to letter-only PDF
      toast.warning('Could not load supporting documents — downloading letters only.', { duration: 4000 });
      handleDownloadPDF();
    } finally {
      setIsGenerating(false);
      setGenerationProgress({ step: '', progress: 0, message: '' });
    }
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

  if (!profileLoading && user?.id && !croaAccepted) {
    return (
      <CROADisclosureModal
        userId={user.id}
        onAccepted={() => {
          clearProfileCache();
          refreshProfile();
        }}
      />
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
              onClose={() => setShowDocsSection(false)}
              onPrepare={handlePreparePacket}
            />
          )}

          {/* Mailing Instructions */}
          {showDocsSection && (
            <MailingInstructions />
          )}
        </CardContent>
      </Card>
      
      {/* Credit Clarity AI Chatbot */}
      <ChatbotWidget />

      {/* Duplicate Dispute Modal */}
      <DuplicateDisputeModal
        open={duplicateModalOpen}
        onClose={() => setDuplicateModalOpen(false)}
        onProceedAnyway={async () => {
          setDuplicateModalOpen(false);
          await proceedWithGeneration();
        }}
        duplicates={duplicateInfo}
      />
    </div>
  );
};

export default DisputeWizardPage;