// File: src/pages/DisputeWizardPage.tsx
"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "sonner";
import { useLocation, useNavigate } from "react-router-dom";
import { DocumentUploadSection } from "@/components/disputes/DocumentUploadSection";
import { MailingInstructions } from "@/components/disputes/MailingInstructions";
import { CreditNavbar } from "@/components/navbar/CreditNavbar";
import { useAuth } from "@/hooks/use-auth";
import { FileText, Package, AlertCircle, User, Loader2, Edit3, Save, X, RefreshCw } from "lucide-react";
import jsPDF from 'jspdf';
import { supabase } from '@/integrations/supabase/client';
import { 
  loadAllTradelinesFromDatabase, 
  getNegativeTradelines, 
  type ParsedTradeline 
} from '@/utils/tradelineParser';
import { usePersistentTradelines } from '@/hooks/usePersistentTradelines';
import { usePersistentProfile } from '@/hooks/usePersistentProfile';
import { TradelinesStatus } from '@/components/ui/tradelines-status';
import { ProfileStatus } from '@/components/ui/profile-status';
import { v4 as uuidv4 } from 'uuid';

// Using DisputeProfile from usePersistentProfile hook
// interface UserProfile is now imported from the hook

interface GeneratedDisputeLetter {
  id: string;
  creditBureau: string;
  tradelines: ParsedTradeline[];
  letterContent: string;
  disputeCount: number;
  isEdited?: boolean;
}

interface PacketProgress {
  step: string;
  progress: number;
  message: string;
}

interface UploadedDocument {
  id: string;
  name: string;
  type: string;
  file: File;
  preview?: string;
}

// Credit Bureau Information
const CREDIT_BUREAU_ADDRESSES = {
  'Experian': {
    name: 'Experian',
    address: 'P.O. Box 4000',
    city: 'Allen',
    state: 'TX',
    zip: '75013'
  },
  'Equifax': {
    name: 'Equifax Information Services LLC',
    address: 'P.O. Box 740256',
    city: 'Atlanta',
    state: 'GA',
    zip: '30374'
  },
  'TransUnion': {
    name: 'TransUnion LLC Consumer Dispute Center',
    address: 'P.O. Box 2000',
    city: 'Chester',
    state: 'PA',
    zip: '19016'
  }
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
  
  // Use persistent profile hook
  const {
    disputeProfile,
    loading: profileLoading,
    error: profileError,
    refreshProfile,
    isProfileComplete,
    missingFields
  } = usePersistentProfile();
  const [negativeTradelines, setNegativeTradelines] = useState<ParsedTradeline[]>([]);
  const [selectedTradelines, setSelectedTradelines] = useState<string[]>([]);
  const [generatedLetters, setGeneratedLetters] = useState<GeneratedDisputeLetter[]>([]);
  const [uploadedDocuments, setUploadedDocuments] = useState<UploadedDocument[]>([]);
  const [generatedPDF, setGeneratedPDF] = useState<Blob | null>(null);
  const [pdfFilename, setPdfFilename] = useState<string>('');
  const [editingLetter, setEditingLetter] = useState<string | null>(null);
  const [editedContent, setEditedContent] = useState<string>('');
  
  // Use persistent tradelines hook
  const {
    tradelines: persistentTradelines,
    loading: tradelinesLoading,
    error: tradelinesError,
    getNegativeTradelines: getPersistentNegativeTradelines,
    refreshTradelines
  } = usePersistentTradelines();

  // Load user data when component mounts
  useEffect(() => {
    if (user?.id) {
      setIsLoading(true);
      // Profile loading is handled by the persistent hook
      // Just set loading to false after hooks are ready
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

  // Show loading state for tradelines and profile
  useEffect(() => {
    if (tradelinesLoading && !isLoading) {
      toast.info('Loading tradelines from database...', {
        description: 'Fetching your credit data'
      });
    }
  }, [tradelinesLoading, isLoading]);

  useEffect(() => {
    if (profileLoading && !isLoading) {
      toast.info('Loading profile information...', {
        description: 'Fetching your personal data'
      });
    }
  }, [profileLoading, isLoading]);

  // Show error state for tradelines and profile
  useEffect(() => {
    if (tradelinesError) {
      toast.error('Failed to load tradelines', {
        description: 'Please try uploading your credit report again'
      });
    }
  }, [tradelinesError]);

  useEffect(() => {
    if (profileError) {
      toast.error('Failed to load profile', {
        description: 'Please check your profile information'
      });
    }
  }, [profileError]);

  // Generate dispute reasons based on tradeline status
  const getDisputeReasons = (tradeline: ParsedTradeline): string[] => {
    const reasons = [];
    const status = tradeline.account_status.toLowerCase();
    
    if (status.includes('charged off')) {
      reasons.push("This account was not charged off and should be reported as current");
      reasons.push("The charge-off information is inaccurate and unverifiable");
    }
    
    if (status.includes('collection')) {
      reasons.push("This account is not in collection and should be removed");
      reasons.push("I never received proper debt validation for this collection account");
    }
    
    if (status.includes('late')) {
      reasons.push("No payments were late on this account");
      reasons.push("The late payment information is inaccurate");
    }
    
    if (tradeline.dispute_count > 0) {
      reasons.push("This account has been previously disputed and remains unverified");
    }
    
    if (reasons.length === 0) {
      reasons.push("This account information is inaccurate and should be corrected or removed");
      reasons.push("The information cannot be verified and should be deleted");
    }
    
    return reasons.slice(0, 3);
  };

  // Generate dispute letter content for multiple tradelines to one bureau
  const generateDisputeLetterContent = (tradelines: ParsedTradeline[], creditBureau: string, profile: NonNullable<typeof disputeProfile>): string => {
    const currentDate = new Date().toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
    
    const bureau = CREDIT_BUREAU_ADDRESSES[creditBureau as keyof typeof CREDIT_BUREAU_ADDRESSES] || CREDIT_BUREAU_ADDRESSES['Experian'];
    
    // Enhanced header with complete profile information
    const headerContact = [
      profile.phoneNumber ? `Phone: ${profile.phoneNumber}` : '',
      profile.email ? `Email: ${profile.email}` : '',
      profile.dateOfBirth ? `Date of Birth: ${profile.dateOfBirth}` : '',
      profile.lastFourSSN ? `SSN: ****${profile.lastFourSSN}` : ''
    ].filter(Boolean).join('\n');
    
    return `${profile.firstName} ${profile.lastName}
${profile.address1}${profile.address2 ? `\n${profile.address2}` : ''}
${profile.city}, ${profile.state} ${profile.zipCode}
${headerContact}

${currentDate}

${bureau.name}
${bureau.address}
${bureau.city}, ${bureau.state} ${bureau.zip}

RE: Formal Dispute of Credit Report Information
Consumer ID: ${profile.lastFourSSN ? `****${profile.lastFourSSN}` : '[Last 4 digits of SSN]'}
Date of Birth: ${profile.dateOfBirth || '[MM/DD/YYYY]'}

Dear Credit Reporting Agency,

I am writing to formally dispute the following information appearing on my credit report, which I believe to be inaccurate, incomplete, outdated, or unverifiable under the Fair Credit Reporting Act (FCRA) Section 611.

As a consumer, I have the right to dispute any information on my credit report that I believe to be inaccurate or incomplete. This dispute is made in good faith and is not frivolous.

DISPUTED ACCOUNT INFORMATION:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
I am disputing the following ${tradelines.length} account(s) appearing on my ${creditBureau} credit report:

${tradelines.map((tradeline, index) => {
  const disputeReasons = getDisputeReasons(tradeline);
  return `ACCOUNT ${index + 1}:
Creditor/Collection Agency: ${tradeline.creditor_name}
Account Number: ${tradeline.account_number}
Account Type: ${tradeline.account_type}
Reported Status: ${tradeline.account_status}
Reported Balance: ${tradeline.account_balance}
Date Opened: ${tradeline.date_opened}
${tradeline.dispute_count > 0 ? `Previous Disputes: ${tradeline.dispute_count}` : ''}

REASON(S) FOR DISPUTE:
${disputeReasons.map((reason, reasonIndex) => `• ${reason}`).join('\n')}
`;
}).join('\n' + '─'.repeat(70) + '\n')}

LEGAL BASIS FOR DISPUTE:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Under the Fair Credit Reporting Act (FCRA), specifically 15 U.S.C. § 1681i, you are required to:
• Investigate disputed information within 30 days of receipt
• Forward all relevant information to the furnisher
• Delete information that cannot be verified as completely accurate
• Provide written results of your investigation

REQUESTED ACTION:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
I hereby request that you:

1. Conduct a reasonable investigation of the disputed information within 30 days
2. Contact the furnisher of this information to verify its complete accuracy
3. Remove this information immediately if it cannot be verified as completely accurate
4. Provide me with written results of your investigation within 30 days
5. If removed, send an updated copy of my credit report at no charge
6. Notify all parties who have received this information in the past 6 months

METHOD OF INVESTIGATION:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Please note that a reasonable investigation requires more than simply forwarding my dispute to the furnisher. You must conduct your own independent verification of the information's accuracy.

SUPPORTING DOCUMENTATION:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
I have enclosed copies of supporting documentation to assist in your investigation, including:
• Copy of driver's license for identity verification
• Proof of current address
• Any relevant account statements or correspondence

CERTIFICATION:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
I certify that the information contained in this dispute letter is true and correct to the best of my knowledge. I understand that any false statements may subject me to civil and criminal penalties.

Please provide me with written results of your investigation within 30 days as required by law. If this information is found to be inaccurate or unverifiable, please delete it entirely and provide me with an updated credit report.

I expect your full cooperation in resolving this matter promptly. Failure to comply with the FCRA may result in additional action being taken.

Thank you for your immediate attention to this matter.

Sincerely,


${profile.firstName} ${profile.lastName}

Enclosures: Supporting Documentation
Date: ${currentDate}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
This letter was generated as part of a lawful credit repair process.
Consumer rights under FCRA § 611, § 623, and § 681i apply.
Please retain this letter for your records.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`;
  };

  // Generate dispute letters grouped by credit bureau
  const generateDisputeLetters = async (): Promise<GeneratedDisputeLetter[]> => {
    if (!disputeProfile) {
      throw new Error("User profile is required to generate dispute letters");
    }

    const letters: GeneratedDisputeLetter[] = [];
    const selectedNegative = negativeTradelines.filter(t => selectedTradelines.includes(t.id));

    // Group tradelines by credit bureau
    const tradelinesByBureau: Record<string, ParsedTradeline[]> = {};
    selectedNegative.forEach(tradeline => {
      const bureau = tradeline.credit_bureau || 'Experian'; // Default to Experian if no bureau specified
      if (!tradelinesByBureau[bureau]) {
        tradelinesByBureau[bureau] = [];
      }
      tradelinesByBureau[bureau].push(tradeline);
    });

    const bureaus = Object.keys(tradelinesByBureau);
    
    for (let i = 0; i < bureaus.length; i++) {
      const bureau = bureaus[i];
      const tradelines = tradelinesByBureau[bureau];
      
      setGenerationProgress({
        step: 'letters',
        progress: ((i + 1) / bureaus.length) * 70,
        message: `Generating dispute letter for ${bureau} (${tradelines.length} accounts)...`
      });

      await new Promise(resolve => setTimeout(resolve, 500));

      const letter: GeneratedDisputeLetter = {
        id: uuidv4(),
        creditBureau: bureau,
        tradelines: tradelines,
        letterContent: generateDisputeLetterContent(tradelines, bureau, disputeProfile),
        disputeCount: tradelines.length
      };

      letters.push(letter);
    }

    return letters;
  };

  // Generate PDF packet
  const generatePDFPacket = async (letters: GeneratedDisputeLetter[]): Promise<Blob> => {
    setGenerationProgress({
      step: 'pdf',
      progress: 70,
      message: 'Creating PDF dispute packet...'
    });

    try {
      const pdf = new jsPDF({
        orientation: 'portrait',
        unit: 'mm',
        format: 'a4'
      });

      const margin = 20;
      const pageWidth = pdf.internal.pageSize.getWidth();
      const maxLineWidth = pageWidth - (margin * 2);

      // Add cover page
      pdf.setFontSize(24);
      pdf.setFont('helvetica', 'bold');
      pdf.text('CREDIT DISPUTE PACKET', pageWidth / 2, 40, { align: 'center' });
      
      pdf.setFontSize(12);
      pdf.setFont('helvetica', 'normal');
      pdf.text(`Generated: ${new Date().toLocaleDateString()}`, pageWidth / 2, 60, { align: 'center' });
      pdf.text(`Credit Bureau Letters: ${letters.length}`, pageWidth / 2, 70, { align: 'center' });
      pdf.text(`Total Disputed Accounts: ${letters.reduce((sum, letter) => sum + letter.disputeCount, 0)}`, pageWidth / 2, 80, { align: 'center' });
      
      if (disputeProfile) {
        pdf.text(`For: ${disputeProfile.firstName} ${disputeProfile.lastName}`, pageWidth / 2, 100, { align: 'center' });
      }

      // Add individual letters
      letters.forEach((letter, index) => {
        setGenerationProgress({
          step: 'pdf',
          progress: 70 + ((index / letters.length) * 25),
          message: `Adding ${letter.creditBureau} letter (${letter.disputeCount} accounts)...`
        });

        pdf.addPage();
        pdf.setFontSize(10);
        pdf.setFont('helvetica', 'normal');
        
        const lines = pdf.splitTextToSize(letter.letterContent, maxLineWidth);
        let yPosition = margin;
        const lineHeight = 5;
        
        lines.forEach((line: string) => {
          if (yPosition > pdf.internal.pageSize.getHeight() - margin) {
            pdf.addPage();
            yPosition = margin;
          }
          
          pdf.text(line, margin, yPosition);
          yPosition += lineHeight;
        });
      });

      setGenerationProgress({
        step: 'pdf',
        progress: 95,
        message: 'Finalizing PDF...'
      });

      return pdf.output('blob');
      
    } catch (error) {
      console.error('[ERROR] PDF generation error:', error);
      throw new Error('Failed to generate PDF packet');
    }
  };

  // Save dispute packet record with correct schema
  const saveDisputePacketRecord = async (letters: GeneratedDisputeLetter[], filename: string) => {
    if (!disputeProfile?.id) {
      console.warn('[WARN] No user profile ID available for saving dispute record');
      return;
    }

    try {
      console.log('[DEBUG] 💾 Saving dispute packet record to database');
      
      // Use the correct table name and column structure
      const { data, error } = await supabase
        .from('dispute_packets') // Make sure this table exists
        .insert({
          id: uuidv4(),
          user_id: disputeProfile.id,
          packet_name: filename,
          letter_count: letters.length,
          tradelines_disputed: JSON.stringify(letters.map(l => ({
            bureau: l.creditBureau,
            accounts: l.tradelines.map(t => ({
              creditor: t.creditor_name,
              account: t.account_number,
              status: t.account_status
            }))
          }))),
          status: 'generated'
        })
        .select()
        .single();

      if (error) {
        console.error('[ERROR] Error saving dispute packet record:', error);
        // Don't throw error, just log it - this shouldn't break the flow
      } else {
        if ('id' in data) {
          console.log(data.id); // ✅ TypeScript now knows `id` exists here
        } 
      }
    } catch (error) {
      console.error('[ERROR] Exception saving dispute packet record:', error);
      // Don't throw error, just log it
    }
  };

  // Handle document upload
  const handleDocumentUpload = (documents: UploadedDocument[]) => {
    setUploadedDocuments(prev => [...prev, ...documents]);
    toast.success(`Added ${documents.length} identity document(s)`);
  };

  // Handle manual PDF download
  const handleDownloadPDF = () => {
    if (!generatedPDF || !pdfFilename) {
      toast.error('No PDF available for download');
      return;
    }

    const url = URL.createObjectURL(generatedPDF);
    const link = document.createElement('a');
    link.href = url;
    link.download = pdfFilename;
    link.style.display = 'none';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);

    toast.success(`Downloaded ${pdfFilename}`);
  };

  // Handle letter editing
  const handleEditLetter = (letterId: string, content: string) => {
    setEditingLetter(letterId);
    setEditedContent(content);
    
    toast.info('Edit mode activated. Make your changes and click "Save Changes" when done.', {
      description: 'The PDF will need to be regenerated after saving changes.'
    });
  };

  const handleSaveEdit = () => {
    if (!editingLetter) return;

    // Basic validation
    if (!editedContent.trim()) {
      toast.error('Letter content cannot be empty');
      return;
    }

    if (editedContent.length < 100) {
      toast.error('Letter content seems too short. Please ensure it contains proper dispute information.');
      return;
    }

    // Update the letter content
    setGeneratedLetters(prev => 
      prev.map(letter => 
        letter.id === editingLetter 
          ? { ...letter, letterContent: editedContent, isEdited: true }
          : letter
      )
    );

    // Clear the generated PDF so it needs to be regenerated with new content
    setGeneratedPDF(null);
    setPdfFilename('');

    // Exit edit mode
    setEditingLetter(null);
    setEditedContent('');

    toast.success('Letter updated successfully. Please regenerate the PDF to include your changes.');
  };

  const handleCancelEdit = () => {
    setEditingLetter(null);
    setEditedContent('');
  };

  // Regenerate PDF with updated content
  const handleRegeneratePDF = async () => {
    if (generatedLetters.length === 0) {
      toast.error('No letters to regenerate');
      return;
    }

    try {
      setGenerationProgress({
        step: 'pdf',
        progress: 0,
        message: 'Regenerating PDF with your changes...'
      });

      const pdfBlob = await generatePDFPacket(generatedLetters);

      const timestamp = new Date().toISOString().split('T')[0];
      const filename = `credit-dispute-packet-${timestamp}.pdf`;
      
      setGeneratedPDF(pdfBlob);
      setPdfFilename(filename);

      setGenerationProgress({
        step: 'complete',
        progress: 100,
        message: 'PDF regenerated successfully!'
      });

      toast.success('PDF regenerated with your changes');

      setTimeout(() => {
        setGenerationProgress({ step: '', progress: 0, message: '' });
      }, 2000);

    } catch (error) {
      console.error('[ERROR] Error regenerating PDF:', error);
      toast.error('Failed to regenerate PDF');
      setGenerationProgress({ step: 'error', progress: 0, message: 'Error regenerating PDF' });
    }
  };

  // Main packet generation logic
  const handleGeneratePacket = async () => {
    if (!disputeProfile) {
      toast.error("Please complete your profile information first");
      navigate('/profile');
      return;
    }

    if (!isProfileComplete) {
      toast.error(`Please complete your profile. Missing: ${missingFields.join(', ')}`);
      navigate('/profile');
      return;
    }

    if (selectedTradelines.length === 0) {
      toast.error("Please select at least one negative tradeline to dispute");
      return;
    }

    if (!disputeProfile.firstName || !disputeProfile.lastName || !disputeProfile.address1) {
      toast.error("Your profile is missing required information (name, address)");
      navigate('/profile');
      return;
    }

    setIsGenerating(true);

    try {
      setGenerationProgress({
        step: 'letters',
        progress: 10,
        message: 'Starting letter generation...'
      });

      const letters = await generateDisputeLetters();
      setGeneratedLetters(letters);

      const pdfBlob = await generatePDFPacket(letters);

      setGenerationProgress({
        step: 'finalizing',
        progress: 98,
        message: 'Finalizing dispute packet...'
      });

      const timestamp = new Date().toISOString().split('T')[0];
      const filename = `credit-dispute-packet-${timestamp}.pdf`;
      
      // Store PDF for manual download
      setGeneratedPDF(pdfBlob);
      setPdfFilename(filename);

      // Save record to database (don't await to avoid blocking)
      saveDisputePacketRecord(letters, filename);

      setGenerationProgress({
        step: 'complete',
        progress: 100,
        message: 'Dispute packet generated successfully!'
      });

      const totalAccounts = letters.reduce((sum, letter) => sum + letter.disputeCount, 0);
      toast.success(`Dispute packet generated! ${letters.length} letter(s) for ${totalAccounts} accounts ready for download`);

      setTimeout(() => {
        setGenerationProgress({ step: '', progress: 0, message: '' });
      }, 3000);

    } catch (error) {
      console.error('[ERROR] Error generating dispute packet:', error);
      toast.error(`Failed to generate dispute packet: ${error instanceof Error ? error.message : 'Unknown error'}`);
      
      setGenerationProgress({ step: 'error', progress: 0, message: 'Error generating packet' });
      setTimeout(() => {
        setGenerationProgress({ step: '', progress: 0, message: '' });
      }, 3000);
    } finally {
      setIsGenerating(false);
    }
  };

  // Toggle tradeline selection
  const toggleTradelineSelection = (tradelineId: string) => {
    setSelectedTradelines(prev => {
      const newSelection = prev.includes(tradelineId) 
        ? prev.filter(id => id !== tradelineId)
        : [...prev, tradelineId];
      
      // Limit to reasonable number of disputes
      if (newSelection.length > 10) {
        toast.warning("We recommend disputing no more than 10 accounts at once for better success rates");
        return prev;
      }
      
      return newSelection;
    });
  };

  const isReadyToGenerate = disputeProfile && isProfileComplete && selectedTradelines.length > 0 && !isLoading && !profileLoading;

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
        <CardHeader>
          <CardTitle className="text-2xl flex items-center gap-2">
            <Package className="h-6 w-6" />
            Generate Dispute Packet
          </CardTitle>
          <p className="text-muted-foreground">
            Create personalized dispute letters for negative tradelines using your profile information
          </p>
        </CardHeader>
        
        <CardContent className="space-y-6">
          
          {/* Requirements Check */}
          {(!disputeProfile || !isProfileComplete) && (
            <Card className="border-yellow-200 bg-yellow-50">
              <CardContent className="p-4">
                <div className="flex items-center gap-2 text-yellow-800">
                  <AlertCircle className="h-5 w-5" />
                  <div>
                    <div className="font-medium">
                      {!disputeProfile ? 'Profile Required' : 'Profile Incomplete'}
                    </div>
                    <div className="text-sm">
                      {!disputeProfile ? 
                        'Complete your profile to generate personalized dispute letters.' :
                        `Missing required fields: ${missingFields.join(', ')}`
                      }{' '}
                      <Button 
                        variant="link" 
                        className="p-0 h-auto text-yellow-800 underline"
                        onClick={() => navigate('/profile')}
                      >
                        {!disputeProfile ? 'Complete Profile' : 'Update Profile'}
                      </Button>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

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
          {disputeProfile && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <User className="h-5 w-5" />
                  Profile Information
                  <Badge variant={isProfileComplete ? "default" : "secondary"} className="ml-auto">
                    {isProfileComplete ? 'Complete' : 'Incomplete'}
                  </Badge>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                  <div><strong>Name:</strong> {disputeProfile.firstName} {disputeProfile.lastName}</div>
                  <div><strong>Address:</strong> {disputeProfile.address1}</div>
                  {disputeProfile.address2 && (
                    <div><strong>Address 2:</strong> {disputeProfile.address2}</div>
                  )}
                  <div><strong>City:</strong> {disputeProfile.city}, {disputeProfile.state} {disputeProfile.zipCode}</div>
                  <div><strong>Phone:</strong> {disputeProfile.phoneNumber || 'Not provided'}</div>
                  <div><strong>Email:</strong> {disputeProfile.email || 'Not provided'}</div>
                  <div><strong>DOB:</strong> {disputeProfile.dateOfBirth || 'Not provided'}</div>
                  <div><strong>SSN:</strong> {disputeProfile.lastFourSSN ? `****${disputeProfile.lastFourSSN}` : 'Not provided'}</div>
                </div>
                {(!disputeProfile.phoneNumber || !disputeProfile.email || !disputeProfile.dateOfBirth || !disputeProfile.lastFourSSN) && (
                  <div className="mt-2 text-sm text-yellow-600">
                    <AlertCircle className="h-4 w-4 inline mr-1" />
                    Consider adding missing information for stronger dispute letters
                  </div>
                )}
                {!isProfileComplete && (
                  <div className="mt-2 text-sm text-red-600">
                    <AlertCircle className="h-4 w-4 inline mr-1" />
                    Missing required fields: {missingFields.join(', ')}
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Negative Tradelines Selection */}
          <Card>
            <CardHeader>
              <div className="flex justify-between items-start">
                <div>
                  <CardTitle className="text-lg">Negative Tradelines to Dispute</CardTitle>
                  <p className="text-sm text-muted-foreground">
                    Select the negative accounts you want to dispute ({selectedTradelines.length} of {negativeTradelines.length} selected)
                    {selectedTradelines.length > 5 && (
                      <span className="text-yellow-600 ml-2">
                        • Consider limiting to 5-10 for better success rates
                      </span>
                    )}
                  </p>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={refreshTradelines}
                  disabled={tradelinesLoading}
                  className="text-xs"
                >
                  {tradelinesLoading ? '🔄' : '📊'} Refresh
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {negativeTradelines.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <AlertCircle className="h-12 w-12 mx-auto mb-4" />
                  <p className="mb-2">No negative tradelines found.</p>
                  <p className="text-sm mb-4">
                    Upload a credit report to identify accounts that can be disputed.
                  </p>
                  <Button 
                    variant="outline" 
                    onClick={() => navigate('/upload')}
                  >
                    Upload Credit Report
                  </Button>
                </div>
              ) : (
                <div className="space-y-3">
                  <div className="flex gap-2 mb-4">
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={() => setSelectedTradelines(negativeTradelines.map(t => t.id))}
                    >
                      Select All ({negativeTradelines.length})
                    </Button>
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={() => setSelectedTradelines([])}
                    >
                      Clear Selection
                    </Button>
                    <div className="ml-auto text-sm text-muted-foreground flex items-center">
                      {selectedTradelines.length} selected
                    </div>
                  </div>

                  {negativeTradelines.map((tradeline) => {
                    const isSelected = selectedTradelines.includes(tradeline.id);
                    const disputeReasons = getDisputeReasons(tradeline);
                    
                    return (
                      <div 
                        key={tradeline.id}
                        className={`
                          border rounded-lg p-4 cursor-pointer transition-all duration-200
                          ${isSelected 
                            ? 'border-primary bg-primary/5 shadow-sm' 
                            : 'border-muted hover:border-primary/50 hover:shadow-sm'
                          }
                        `}
                        onClick={() => toggleTradelineSelection(tradeline.id)}
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-2">
                              <input
                                type="checkbox"
                                checked={isSelected}
                                onChange={() => toggleTradelineSelection(tradeline.id)}
                                className="rounded"
                              />
                              <h4 className="font-medium">{tradeline.creditor_name}</h4>
                              <Badge variant="destructive">Negative</Badge>
                              {tradeline.dispute_count > 0 && (
                                <Badge variant="secondary">
                                  Disputed {tradeline.dispute_count}x
                                </Badge>
                              )}
                            </div>
                            
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-sm text-muted-foreground mb-2">
                              <div><strong>Account:</strong> {tradeline.account_number}</div>
                              <div><strong>Status:</strong> {tradeline.account_status}</div>
                              <div><strong>Balance:</strong> {tradeline.account_balance}</div>
                              <div><strong>Bureau:</strong> {tradeline.credit_bureau}</div>
                            </div>

                            {isSelected && (
                              <div className="mt-2 p-2 bg-muted/50 rounded text-xs">
                                <strong>Dispute Strategy:</strong>
                                <ul className="mt-1 space-y-1">
                                  {disputeReasons.map((reason, idx) => (
                                    <li key={idx} className="flex items-start">
                                      <span className="w-2 h-2 bg-primary rounded-full mt-1.5 mr-2 flex-shrink-0" />
                                      {reason}
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Identity Documents */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Identity Documents (Recommended)</CardTitle>
              <p className="text-sm text-muted-foreground">
                Add identity documents to strengthen your dispute letters and verify your identity
              </p>
            </CardHeader>
            <CardContent>
              {!showDocsSection ? (
                <Button 
                  variant="outline"
                  onClick={() => setShowDocsSection(true)}
                >
                  <FileText className="h-4 w-4 mr-2" />
                  Add Identity Documents
                </Button>
              ) : (
                <div className="space-y-4">
                  <DocumentUploadSection 
                    onClose={() => setShowDocsSection(false)}
                    onUpload={handleDocumentUpload}
                  />
                  
                  {uploadedDocuments.length > 0 && (
                    <div className="space-y-2">
                      <h4 className="font-medium flex items-center gap-2">
                        <FileText className="h-4 w-4 text-green-600" />
                        Uploaded Documents ({uploadedDocuments.length})
                      </h4>
                      {uploadedDocuments.map((doc) => (
                        <div key={doc.id} className="flex items-center justify-between p-3 border rounded bg-green-50">
                          <div className="flex items-center gap-2">
                            <FileText className="h-4 w-4 text-green-600" />
                            <span className="text-sm font-medium">{doc.name}</span>
                            <Badge variant="secondary">{doc.type}</Badge>
                          </div>
                          <Button 
                            variant="ghost" 
                            size="sm"
                            onClick={() => setUploadedDocuments(prev => prev.filter(d => d.id !== doc.id))}
                          >
                            Remove
                          </Button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Generation Progress */}
          {isGenerating && (
            <Card className="border-blue-200 bg-blue-50">
              <CardContent className="p-4">
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="font-medium flex items-center gap-2">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Generating Dispute Packet...
                    </span>
                    <span className="text-sm text-muted-foreground">
                      {generationProgress.progress}%
                    </span>
                  </div>
                  <Progress value={generationProgress.progress} className="w-full" />
                  <p className="text-sm text-muted-foreground">
                    {generationProgress.message}
                  </p>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Mailing Instructions */}
          <MailingInstructions />

          {/* Generate Button */}
          <div className="flex justify-center">
            <Button 
              onClick={handleGeneratePacket}
              disabled={!isReadyToGenerate || isGenerating}
              size="lg"
              className="min-w-[300px]"
            >
              {isGenerating ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Generating Letters...
                </>
              ) : (
                <>
                  <FileText className="h-4 w-4 mr-2" />
                  Generate Dispute Letters ({selectedTradelines.length} accounts)
                </>
              )}
            </Button>
          </div>

          {/* Preview Generated Letters */}
          {generatedLetters.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <FileText className="h-5 w-5 text-green-600" />
                  Generated Dispute Letters ({generatedLetters.length} bureau{generatedLetters.length > 1 ? 's' : ''})
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {generatedLetters.map((letter, index) => (
                    <div key={letter.id} className="border rounded-lg overflow-hidden">
                      <div className="flex items-center justify-between p-4 bg-muted/30">
                        <div>
                          <h4 className="font-medium">Letter {index + 1}: {letter.creditBureau}</h4>
                          <div className="text-sm text-muted-foreground">
                            {letter.disputeCount} account{letter.disputeCount > 1 ? 's' : ''} • {letter.tradelines.map(t => t.creditor_name).join(', ')}
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleEditLetter(letter.id, letter.letterContent)}
                            disabled={editingLetter === letter.id}
                          >
                            <Edit3 className="h-3 w-3 mr-1" />
                            Edit
                          </Button>
                          <Badge variant={letter.isEdited ? "default" : "outline"}>
                            {letter.isEdited ? 'Edited' : 'Ready to Mail'}
                          </Badge>
                        </div>
                      </div>
                      <div className="p-4 border-t">
                        <details className="text-sm">
                          <summary className="cursor-pointer font-medium mb-2 hover:text-primary">
                            View Letter Content & Disputed Accounts
                          </summary>
                          <div className="mt-3 space-y-3">
                            <div>
                              <strong>Disputed Accounts:</strong>
                              <div className="mt-1 space-y-1">
                                {letter.tradelines.map((tradeline, idx) => (
                                  <div key={idx} className="text-muted-foreground text-xs">
                                    {idx + 1}. {tradeline.creditor_name} - {tradeline.account_number} ({tradeline.account_status})
                                  </div>
                                ))}
                              </div>
                            </div>
                            <div>
                              <strong>Full Letter:</strong>
                              {editingLetter === letter.id ? (
                                <div className="mt-2 space-y-2">
                                  <Textarea
                                    value={editedContent}
                                    onChange={(e) => setEditedContent(e.target.value)}
                                    className="min-h-[400px] text-xs font-mono"
                                    placeholder="Edit letter content..."
                                  />
                                  <div className="flex justify-between items-center">
                                    <div className="flex gap-2">
                                      <Button
                                        size="sm"
                                        onClick={handleSaveEdit}
                                        className="bg-green-600 hover:bg-green-700"
                                      >
                                        <Save className="h-3 w-3 mr-1" />
                                        Save Changes
                                      </Button>
                                      <Button
                                        size="sm"
                                        variant="outline"
                                        onClick={handleCancelEdit}
                                      >
                                        <X className="h-3 w-3 mr-1" />
                                        Cancel
                                      </Button>
                                    </div>
                                    <div className="text-xs text-muted-foreground">
                                      {editedContent.length} characters
                                    </div>
                                  </div>
                                </div>
                              ) : (
                                <pre className="whitespace-pre-wrap bg-muted p-3 rounded text-xs mt-1 overflow-x-auto">
                                  {letter.letterContent}
                                </pre>
                              )}
                            </div>
                          </div>
                        </details>
                      </div>
                    </div>
                  ))}
                  
                  {/* Download Section */}
                  <div className="text-center p-4 bg-green-50 rounded-lg">
                    <FileText className="h-8 w-8 text-green-600 mx-auto mb-2" />
                    <p className="font-medium text-green-800">Dispute packet ready!</p>
                    <p className="text-sm text-green-600 mb-4">
                      Print, sign, and mail each letter to the appropriate credit bureau using certified mail.
                    </p>
                    
                    <div className="flex flex-col gap-2">
                      {!generatedPDF ? (
                        <Button 
                          onClick={handleRegeneratePDF}
                          className="bg-blue-600 hover:bg-blue-700 text-white"
                          size="lg"
                          disabled={isGenerating}
                        >
                          <RefreshCw className="h-4 w-4 mr-2" />
                          Generate PDF Packet
                        </Button>
                      ) : (
                        <div className="flex gap-2">
                          <Button 
                            onClick={handleDownloadPDF}
                            className="bg-green-600 hover:bg-green-700 text-white"
                            size="lg"
                          >
                            <FileText className="h-4 w-4 mr-2" />
                            Download PDF Packet ({pdfFilename})
                          </Button>
                          <Button 
                            onClick={handleRegeneratePDF}
                            variant="outline"
                            size="lg"
                            disabled={isGenerating}
                          >
                            <RefreshCw className="h-4 w-4 mr-2" />
                            Regenerate PDF
                          </Button>
                        </div>
                      )}
                      
                      {!generatedPDF && (
                        <p className="text-xs text-muted-foreground">
                          Generate PDF after making any edits to include your changes
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default DisputeWizardPage;