// File: src/pages/DisputeWizardPage.tsx
"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { toast } from "sonner";
import { useLocation, useNavigate } from "react-router-dom";
import { DocumentUploadSection } from "@/components/disputes/DocumentUploadSection";
import { MailingInstructions } from "@/components/disputes/MailingInstructions";
import { CreditNavbar } from "@/components/navbar/CreditNavbar";
import { useAuth } from "@/hooks/use-auth";
import { FileText, Package, AlertCircle, User, Loader2 } from "lucide-react";
import jsPDF from 'jspdf';
import { supabase } from '@/integrations/supabase/client';
import { 
  loadTradelinesFromDatabase, 
  getNegativeTradelines, 
  type ParsedTradeline 
} from '@/utils/tradelineParser';
import { v4 as uuidv4 } from 'uuid';

interface UserProfile {
  id: string;
  firstName: string;
  lastName: string;
  address: string;
  city: string;
  state: string;
  zipCode: string;
  ssn?: string;
  dateOfBirth?: string;
  phone?: string;
  email?: string;
}

interface GeneratedDisputeLetter {
  id: string;
  creditorName: string;
  accountNumber: string;
  disputeReason: string;
  letterContent: string;
  creditBureau: string;
  tradeline: ParsedTradeline;
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
  
  // Data
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null);
  const [negativeTradelines, setNegativeTradelines] = useState<ParsedTradeline[]>([]);
  const [selectedTradelines, setSelectedTradelines] = useState<string[]>([]);
  const [generatedLetters, setGeneratedLetters] = useState<GeneratedDisputeLetter[]>([]);
  const [uploadedDocuments, setUploadedDocuments] = useState<UploadedDocument[]>([]);

  // Load user profile and tradelines from database
  useEffect(() => {
    const loadUserData = async () => {
      if (!user?.id) {
        setIsLoading(false);
        return;
      }

      try {
        setIsLoading(true);
        console.log('[DEBUG] 🔄 Loading user data for:', user.id);

        // Load user profile from Supabase
        const { data: profile, error: profileError } = await supabase
          .from('user_profiles')
          .select('*')
          .eq('user_id', user.id)
          .single();

        if (profileError) {
          if (profileError.code === 'PGRST116') {
            console.log('[INFO] No user profile found, user needs to complete profile');
            toast.info("Please complete your profile to generate dispute letters");
          } else {
            console.error('[ERROR] Failed to load profile:', profileError);
            toast.error("Failed to load user profile");
          }
          setIsLoading(false);
          return;
        }

        if (profile) {
          const userProfileData: UserProfile = {
            id: profile.id,
            firstName: profile.first_name,
            lastName: profile.last_name,
            address1: profile.address1 || '',
            address2: profile.address2 || '',
            city: profile.city || '',
            state: profile.state || '',
            zipCode: profile.zip_code || '',
            ssn: profile.last_four_of_ssn ? `****${profile.last_four_of_ssn}` : undefined,
            dateOfBirth: profile.dob,
            phone: profile.phone_number
          };
          
          setUserProfile(userProfileData);
          console.log('[SUCCESS] ✅ User profile loaded:', userProfileData.firstName, userProfileData.lastName);

          // Load tradelines using the fixed parser
          const allTradelines = await loadTradelinesFromDatabase(user.id);
          console.log('[DEBUG] 📊 Loaded tradelines:', allTradelines.length);

          // Filter negative tradelines
          const negative = getNegativeTradelines(allTradelines);
          console.log('[DEBUG] 🔴 Negative tradelines:', negative.length);

          setNegativeTradelines(negative);
          setSelectedTradelines(negative.map(t => t.id));
        }

      } catch (error) {
        console.error('[ERROR] Error loading user data:', error);
        toast.error("Failed to load user data");
      } finally {
        setIsLoading(false);
      }
    };

    loadUserData();
  }, [user?.id]);

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

  // Generate dispute letter content
  const generateDisputeLetterContent = (tradeline: ParsedTradeline, profile: UserProfile): string => {
    const currentDate = new Date().toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
    
    const disputeReasons = getDisputeReasons(tradeline);
    const bureau = CREDIT_BUREAU_ADDRESSES[tradeline.credit_bureau as keyof typeof CREDIT_BUREAU_ADDRESSES] || CREDIT_BUREAU_ADDRESSES['Experian'];
    
    return `${profile.firstName} ${profile.lastName}
${profile.address}
${profile.city}, ${profile.state} ${profile.zipCode}
${profile.phone ? `Phone: ${profile.phone}` : ''}
${profile.email ? `Email: ${profile.email}` : ''}

${currentDate}

${bureau.name}
${bureau.address}
${bureau.city}, ${bureau.state} ${bureau.zip}

RE: Formal Dispute of Credit Report Information
SSN: ${profile.ssn ? profile.ssn : '[Last 4 digits of SSN]'}
Date of Birth: ${profile.dateOfBirth || '[MM/DD/YYYY]'}

Dear Credit Reporting Agency,

I am writing to formally dispute the following information appearing on my credit report, which I believe to be inaccurate, incomplete, outdated, or unverifiable under the Fair Credit Reporting Act (FCRA) Section 611.

DISPUTED ACCOUNT INFORMATION:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Creditor/Collection Agency: ${tradeline.creditor_name}
Account Number: ${tradeline.account_number}
Account Type: ${tradeline.account_type}
Reported Status: ${tradeline.account_status}
Reported Balance: ${tradeline.account_balance}
Date Opened: ${tradeline.date_opened}
Credit Bureau: ${tradeline.credit_bureau}

REASON(S) FOR DISPUTE:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
${disputeReasons.map((reason, index) => `${index + 1}. ${reason}`).join('\n')}

REQUESTED ACTION:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Under 15 USC § 1681i of the Fair Credit Reporting Act, I hereby request that you:

1. Conduct a reasonable investigation of the disputed information within 30 days
2. Contact the furnisher of this information to verify its complete accuracy
3. Remove this information immediately if it cannot be verified as completely accurate
4. Provide me with written results of your investigation
5. If removed, send an updated copy of my credit report at no charge

I understand that you must reinvestigate the disputed information unless you determine it to be frivolous. The furnisher must conduct a reasonable investigation and report the results back to you. If the information cannot be verified as completely accurate, it must be deleted.

SUPPORTING DOCUMENTATION:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
I have enclosed copies of supporting documentation to assist in your investigation.

Please provide me with written results of your investigation within 30 days as required by law. If this information is found to be inaccurate or unverifiable, please delete it entirely and provide me with an updated credit report.

I expect your full cooperation in resolving this matter promptly. Failure to comply with the FCRA may result in additional action being taken.

Thank you for your immediate attention to this matter.

Sincerely,


${profile.firstName} ${profile.lastName}

Enclosures: Supporting Documentation
Date: ${currentDate}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
This letter was generated as part of a lawful credit repair process.
Consumer rights under FCRA § 611, § 623, and § 681i apply.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`;
  };

  // Generate dispute letters
  const generateDisputeLetters = async (): Promise<GeneratedDisputeLetter[]> => {
    if (!userProfile) {
      throw new Error("User profile is required to generate dispute letters");
    }

    const letters: GeneratedDisputeLetter[] = [];
    const selectedNegative = negativeTradelines.filter(t => selectedTradelines.includes(t.id));

    for (let i = 0; i < selectedNegative.length; i++) {
      const tradeline = selectedNegative[i];
      
      setGenerationProgress({
        step: 'letters',
        progress: ((i + 1) / selectedNegative.length) * 70,
        message: `Generating dispute letter for ${tradeline.creditor_name}...`
      });

      await new Promise(resolve => setTimeout(resolve, 300));

      const letter: GeneratedDisputeLetter = {
        id: uuidv4(), // Use proper UUID
        creditorName: tradeline.creditor_name,
        accountNumber: tradeline.account_number,
        disputeReason: getDisputeReasons(tradeline).join('; '),
        letterContent: generateDisputeLetterContent(tradeline, userProfile),
        creditBureau: tradeline.credit_bureau,
        tradeline: tradeline
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
      pdf.text(`Letters: ${letters.length}`, pageWidth / 2, 70, { align: 'center' });
      
      if (userProfile) {
        pdf.text(`For: ${userProfile.firstName} ${userProfile.lastName}`, pageWidth / 2, 90, { align: 'center' });
      }

      // Add individual letters
      letters.forEach((letter, index) => {
        setGenerationProgress({
          step: 'pdf',
          progress: 70 + ((index / letters.length) * 25),
          message: `Adding letter ${index + 1} of ${letters.length}...`
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
    if (!userProfile?.id) {
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
          user_id: userProfile.id,
          packet_name: filename,
          letter_count: letters.length,
          tradelines_disputed: JSON.stringify(letters.map(l => ({
            creditor: l.creditorName,
            account: l.accountNumber,
            reason: l.disputeReason,
            bureau: l.creditBureau
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

  // Main packet generation logic
  const handleGeneratePacket = async () => {
    if (!userProfile) {
      toast.error("Please complete your profile information first");
      navigate('/profile');
      return;
    }

    if (selectedTradelines.length === 0) {
      toast.error("Please select at least one negative tradeline to dispute");
      return;
    }

    if (!userProfile.firstName || !userProfile.lastName || !userProfile.address) {
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
        step: 'download',
        progress: 98,
        message: 'Preparing download...'
      });

      const timestamp = new Date().toISOString().split('T')[0];
      const filename = `credit-dispute-packet-${timestamp}.pdf`;
      
      const url = URL.createObjectURL(pdfBlob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      link.style.display = 'none';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);

      // Save record to database (don't await to avoid blocking)
      saveDisputePacketRecord(letters, filename);

      setGenerationProgress({
        step: 'complete',
        progress: 100,
        message: 'Dispute packet generated successfully!'
      });

      toast.success(`Dispute packet generated! ${letters.length} letters created and downloaded as ${filename}`);

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

  const isReadyToGenerate = userProfile && selectedTradelines.length > 0 && !isLoading;

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background text-foreground py-10 px-4 md:px-10">
        <CreditNavbar />
        <Card className="max-w-6xl mx-auto">
          <CardContent className="p-8">
            <div className="flex items-center justify-center space-x-2">
              <Loader2 className="h-6 w-6 animate-spin" />
              <span>Loading your credit data...</span>
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
          {!userProfile && (
            <Card className="border-yellow-200 bg-yellow-50">
              <CardContent className="p-4">
                <div className="flex items-center gap-2 text-yellow-800">
                  <AlertCircle className="h-5 w-5" />
                  <div>
                    <div className="font-medium">Profile Required</div>
                    <div className="text-sm">
                      Complete your profile to generate personalized dispute letters.{' '}
                      <Button 
                        variant="link" 
                        className="p-0 h-auto text-yellow-800 underline"
                        onClick={() => navigate('/profile')}
                      >
                        Complete Profile
                      </Button>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Profile Summary */}
          {userProfile && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <User className="h-5 w-5" />
                  Profile Information
                  <Badge variant="outline" className="ml-auto">Verified</Badge>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                  <div><strong>Name:</strong> {userProfile.firstName} {userProfile.lastName}</div>
                  <div><strong>Address:</strong> {userProfile.address}</div>
                  <div><strong>City:</strong> {userProfile.city}, {userProfile.state} {userProfile.zipCode}</div>
                  <div><strong>Phone:</strong> {userProfile.phone || 'Not provided'}</div>
                  <div><strong>Email:</strong> {userProfile.email || 'Not provided'}</div>
                  <div><strong>DOB:</strong> {userProfile.dateOfBirth || 'Not provided'}</div>
                </div>
                {(!userProfile.phone || !userProfile.email || !userProfile.dateOfBirth) && (
                  <div className="mt-2 text-sm text-yellow-600">
                    <AlertCircle className="h-4 w-4 inline mr-1" />
                    Consider adding missing information for stronger dispute letters
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Negative Tradelines Selection */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Negative Tradelines to Dispute</CardTitle>
              <p className="text-sm text-muted-foreground">
                Select the negative accounts you want to dispute ({selectedTradelines.length} of {negativeTradelines.length} selected)
                {selectedTradelines.length > 5 && (
                  <span className="text-yellow-600 ml-2">
                    • Consider limiting to 5-10 for better success rates
                  </span>
                )}
              </p>
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
                  Generate Professional Dispute Letters ({selectedTradelines.length})
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
                  Generated Dispute Letters ({generatedLetters.length})
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {generatedLetters.map((letter, index) => (
                    <div key={letter.id} className="border rounded-lg overflow-hidden">
                      <div className="flex items-center justify-between p-4 bg-muted/30">
                        <div>
                          <h4 className="font-medium">Letter {index + 1}: {letter.creditorName}</h4>
                          <div className="text-sm text-muted-foreground">
                            Account: {letter.accountNumber} • Bureau: {letter.creditBureau}
                          </div>
                        </div>
                        <Badge variant="outline">Ready to Mail</Badge>
                      </div>
                      <div className="p-4 border-t">
                        <details className="text-sm">
                          <summary className="cursor-pointer font-medium mb-2 hover:text-primary">
                            View Letter Content & Dispute Strategy
                          </summary>
                          <div className="mt-3 space-y-3">
                            <div>
                              <strong>Dispute Reasons:</strong>
                              <div className="mt-1 text-muted-foreground">{letter.disputeReason}</div>
                            </div>
                            <div>
                              <strong>Full Letter:</strong>
                              <pre className="whitespace-pre-wrap bg-muted p-3 rounded text-xs mt-1 overflow-x-auto">
                                {letter.letterContent}
                              </pre>
                            </div>
                          </div>
                        </details>
                      </div>
                    </div>
                  ))}
                  
                  <div className="text-center p-4 bg-green-50 rounded-lg">
                    <FileText className="h-8 w-8 text-green-600 mx-auto mb-2" />
                    <p className="font-medium text-green-800">Dispute packet ready!</p>
                    <p className="text-sm text-green-600">
                      Print, sign, and mail each letter to the appropriate credit bureau using certified mail.
                    </p>
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