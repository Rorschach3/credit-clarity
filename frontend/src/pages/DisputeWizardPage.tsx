<<<<<<< Updated upstream:src/pages/DisputeWizardPage.tsx
"use client";
import React, { useState, ChangeEvent } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { toast } from "@/components/ui/use-toast";
import { analyzeDisputeText, generateDisputeLetter, saveTradelines } from "@/services/aiService";
import type { Account, UserData } from "@/schemas/ai";
import { useAuth } from "@/hooks/use-auth";

export default function DisputeWizardPage() {
  const { user } = useAuth();
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [selected, setSelected] = useState<Account[]>([]);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [letter, setLetter] = useState("");
  const [name, setName] = useState("");
  const [address, setAddress] = useState("");

  const handleFileUpload = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return toast({ title: "No file", description: "Select a PDF." });
    if (file.type !== "application/pdf")
      return toast({ title: "Invalid", description: "Only PDFs allowed." });

    setUploading(true);
    setUploadProgress(0);
    setAccounts([]);
    setSelected([]);

    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onloadend = async () => {
      const dataUrl = reader.result;
      if (typeof dataUrl !== "string") {
        setUploading(false);
        return toast({ title: "Error", description: "Could not read file." });
      }
      setUploadProgress(50);
      try {
        // Call the new service:
        const analysis = await analyzeDisputeText(dataUrl);
        setAccounts(analysis.accounts);
        toast({
          title: "Extraction Complete",
          description: `Found ${analysis.accounts.length} accounts.`,
        });
      } catch (err: any) {
        toast({ title: "Extraction Failed", description: err.message });
      } finally {
        setUploadProgress(100);
        setUploading(false);
      }
    };
    reader.onerror = () => {
      setUploading(false);
      toast({ title: "Read Error", description: "Failed to load file." });
    };
  };

  const toggleSelect = (acct: Account) => {
    setSelected((prev) =>
      prev.some((a) => a.accountNumber === acct.accountNumber)
        ? prev.filter((a) => a.accountNumber !== acct.accountNumber)
        : [...prev, acct]
    );
  };

  const generateLetterHandler = async () => {
    if (!user) return toast({ title: "Not signed in", description: "" });
    if (!name || !address || selected.length === 0)
      return toast({ title: "Missing Info", description: "Enter name, address & pick accounts." });

    const userData: UserData = { name, address };
    try {
      // Save tradelines in the database
      await saveTradelines(selected, user.id);
      // Generate the dispute letter
      const { letter: content } = await generateDisputeLetter(selected, userData);
      setLetter(content);
    } catch (err: any) {
      toast({ title: "Error", description: err.message });
    }
  };

  return (
    <div className="min-h-screen bg-background text-foreground p-6">
      <Card className="max-w-3xl mx-auto space-y-6">
        <CardHeader>
          <CardTitle>Dispute Wizard</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label htmlFor="pdf-upload">Upload Credit Report</Label>
            <Input
              id="pdf-upload"
              type="file"
              accept="application/pdf"
              onChange={handleFileUpload}
              disabled={uploading}
            />
            {uploading && <Progress value={uploadProgress} className="mt-2" />}
          </div>

          {accounts.length > 0 && (
            <div>
              <Label>Select Accounts to Dispute</Label>
              <div className="space-y-3 mt-2">
                {accounts.map((a) => {
                  const isSelected = selected.some((s) => s.accountNumber === a.accountNumber);
                  return (
                    <div
                      key={a.accountNumber}
                      className={`p-4 border rounded-lg cursor-pointer ${
                        isSelected ? "border-destructive bg-destructive/10" : ""
                      }`}
                      onClick={() => toggleSelect(a)}
                    >
                      <strong>{a.creditorName}</strong>
                      <br />
                      Account #: {a.accountNumber}
                      <br />
                      Status: {a.accountStatus}
                      <br />
                      Balance:{" "}
                      {a.accountBalance !== undefined ? `$${a.accountBalance.toFixed(2)}` : "N/A"}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <Label htmlFor="name">Your Name</Label>
              <Input id="name" value={name} onChange={(e) => setName(e.target.value)} />
            </div>
            <div>
              <Label htmlFor="address">Address</Label>
              <Input id="address" value={address} onChange={(e) => setAddress(e.target.value)} />
            </div>
          </div>

          <Button
            onClick={generateLetterHandler}
            disabled={!name || !address || selected.length === 0}
          >
            Generate Letter
          </Button>

          {letter && (
            <div className="space-y-2">
              <Label>Generated Letter</Label>
              <Textarea readOnly rows={12} value={letter} className="font-mono" />
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
=======
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
import ChatbotWidget from "@/components/ChatbotWidget";

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
      
      {/* Credit Clarity AI Chatbot */}
      <ChatbotWidget />
    </div>
  );
};

export default DisputeWizardPage;
>>>>>>> Stashed changes:frontend/src/pages/DisputeWizardPage.tsx
