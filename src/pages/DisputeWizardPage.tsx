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
import { FileText, Package, AlertCircle, User } from "lucide-react";
import jsPDF from 'jspdf';
import { supabase } from "@/integrations/supabase/client";

interface UserProfile {
  firstName: string;
  lastName: string;
  address1: string;
  address2?: string;
  city: string;
  state: string;
  zipCode: string;
  lastFourOfSSN?: string;
  dateOfBirth?: string;
  phoneNumber?: string;
}

interface Tradeline {
  id: string;
  creditor_name: string;
  account_number: string;
  account_balance: string;
  account_status: string;
  account_type: string;
  date_opened: string;
  is_negative: boolean;
  credit_bureau: string;
  dispute_count: number;
}

interface GeneratedDisputeLetter {
  id: string;
  creditorName: string;
  accountNumber: string;
  disputeReason: string;
  letterContent: string;
  creditBureau: string;
  tradeline: Tradeline;
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

const DisputeWizardPage = () => {
  const { user } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  
  // State management
  const [showDocsSection, setShowDocsSection] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationProgress, setGenerationProgress] = useState<PacketProgress>({
    step: '',
    progress: 0,
    message: ''
  });
  
  // Data
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null);
  const [negativeTradelines, setNegativeTradelines] = useState<Tradeline[]>([]);
  const [selectedTradelines, setSelectedTradelines] = useState<string[]>([]);
  const [generatedLetters, setGeneratedLetters] = useState<GeneratedDisputeLetter[]>([]);
  const [uploadedDocuments, setUploadedDocuments] = useState<UploadedDocument[]>([]);

  // Load user profile and tradelines
  useEffect(() => {
    const loadUserData = async () => {
      try {
        // Load user profile from database
        if (!user?.id) return;
        
        const { data: profileData, error: profileError } = await supabase
          .from('profiles')
          .select('*')
          .eq('user_id', user.id)
          .single();

        if (profileError) {
          console.error('Error loading profile:', profileError);
        } else if (profileData) {
          setUserProfile({
            firstName: profileData.first_name || '',
            lastName: profileData.last_name || '',
            address1: profileData.address1 || '',
            address2: profileData.address2 || '',
            city: profileData.city || '',
            state: profileData.state || '',
            zipCode: profileData.zip_code?.toString() || '',
            lastFourOfSSN: profileData.lastFourOfSSN ? profileData.lastFourOfSSN.slice(-4) : undefined,
            dateOfBirth: profileData.dob ? new Date(profileData.dob).toLocaleDateString() : undefined,
            phoneNumber: profileData.phone_number || ''
          });
        }

        // Load tradelines from database
        const { data: tradelines, error: tradelinesError } = await supabase
          .from('tradelines')
          .select('*')
          .eq('user_id', user.id);

        if (tradelinesError) {
          console.error('Error loading tradelines:', tradelinesError);
          toast.error("Failed to load tradelines");
        } else if (tradelines) {
          // Transform and filter negative tradelines
          const transformedTradelines: Tradeline[] = tradelines.map(t => ({
            id: t.id || '',
            creditor_name: t.creditor_name || '',
            account_number: t.account_number || '',
            account_balance: t.account_balance || '$0',
            account_status: t.account_status || '',
            account_type: t.account_type || '',
            date_opened: t.date_opened || 'xx/xx/xxxx',
            is_negative: t.is_negative || false,
            credit_bureau: t.credit_bureau || '',
            dispute_count: t.dispute_count || 0
          }));
          
          const negative = transformedTradelines.filter(t => 
            t.is_negative || 
            ['charged off', 'collection', 'late', 'delinquent', 'closed'].some(status => 
              t.account_status.toLowerCase().includes(status)
            )
          );

          setNegativeTradelines(negative);
          setSelectedTradelines(negative.map(t => t.id));
        }

      } catch (error) {
        console.error('Error loading user data:', error);
        toast.error("Failed to load user data");
      }
    };

    if (user?.id) {
      loadUserData();
    }
  }, [user?.id, location.state]);

  // Generate dispute letter content
  const generateDisputeLetterContent = (tradeline: Tradeline, profile: UserProfile): string => {
    const currentDate = new Date().toLocaleDateString();
    const disputeReasons = getDisputeReasons(tradeline);
    
    return `
${profile.firstName} ${profile.lastName}
${profile.address1}
${profile.address2}
${profile.city}, ${profile.state} ${profile.zipCode}
${profile.phoneNumber || ''}

${currentDate}

${tradeline.credit_bureau} Credit Bureau
P.O. Box [Bureau Address]
[City, State ZIP]

RE: Dispute of Credit Report Information
SSN: ${profile.lastFourOfSSN ? `XXX-XX-${profile.lastFourOfSSN}` : '[SSN]'}
DOB: ${profile.dateOfBirth || '[Date of Birth]'}

Dear Credit Reporting Agency,

I am writing to dispute the following information on my credit report, which I believe to be inaccurate, incomplete, or unverifiable:

ACCOUNT INFORMATION TO DISPUTE:
Creditor: ${tradeline.creditor_name}
Account Number: ${tradeline.account_number}
Account Type: ${tradeline.account_type}
Status: ${tradeline.account_status}
Balance: ${tradeline.account_balance}

REASON FOR DISPUTE:
${disputeReasons.join('. ')}

Under the Fair Credit Reporting Act (FCRA), I have the right to dispute incomplete or inaccurate information. I request that you:

1. Conduct a reasonable investigation of this disputed information
2. Contact the furnisher of this information to verify its accuracy
3. Remove or correct this information if it cannot be verified
4. Provide me with the results of your investigation within 30 days

I have enclosed copies of supporting documentation. Please investigate this matter and correct my credit report accordingly.

If you find that the disputed information is inaccurate, incomplete, or cannot be verified, please remove it from my credit report and send me a corrected copy of my credit report.

I look forward to your prompt response and resolution of this matter.

Sincerely,

${profile.firstName} ${profile.lastName}

Enclosures: Supporting Documentation
    `.trim();
  };

  // Get dispute reasons based on tradeline status
  const getDisputeReasons = (tradeline: Tradeline): string[] => {
    const reasons = [];
    
    if (tradeline.account_status.toLowerCase().includes('charged off')) {
      reasons.push("This account was not charged off and should be reported as current");
    }
    
    if (tradeline.account_status.toLowerCase().includes('collection')) {
      reasons.push("This account is not in collection and should be removed");
    }
    
    if (tradeline.account_status.toLowerCase().includes('late')) {
      reasons.push("No payments were late on this account");
    }
    
    if (tradeline.dispute_count > 0) {
      reasons.push("This account has been previously disputed and should be removed");
    }
    
    if (reasons.length === 0) {
      reasons.push("This account information is inaccurate and should be corrected or removed");
    }
    
    return reasons;
  };

  // Generate dispute letters for selected tradelines
  const generateDisputeLetters = async (): Promise<GeneratedDisputeLetter[]> => {
    if (!userProfile) {
      throw new Error("User profile is required to generate dispute letters");
    }

    setGenerationProgress({
      step: 'letters',
      progress: 0,
      message: 'Analyzing negative tradelines...'
    });

    const letters: GeneratedDisputeLetter[] = [];
    const selectedNegative = negativeTradelines.filter(t => selectedTradelines.includes(t.id));

    for (let i = 0; i < selectedNegative.length; i++) {
      const tradeline = selectedNegative[i];
      
      setGenerationProgress({
        step: 'letters',
        progress: ((i + 1) / selectedNegative.length) * 50,
        message: `Generating dispute letter for ${tradeline.creditor_name}...`
      });

      // Real processing - no artificial delay needed

      const letter: GeneratedDisputeLetter = {
        id: `letter-${tradeline.id}`,
        creditorName: tradeline.creditor_name,
        accountNumber: tradeline.account_number,
        disputeReason: getDisputeReasons(tradeline).join(', '),
        letterContent: generateDisputeLetterContent(tradeline, userProfile),
        creditBureau: tradeline.credit_bureau || 'Experian',
        tradeline: tradeline
      };

      letters.push(letter);
    }

    return letters;
  };

  // Generate PDF packet with letters
  const generatePDFPacket = async (letters: GeneratedDisputeLetter[]): Promise<Blob> => {
    setGenerationProgress({
      step: 'pdf',
      progress: 50,
      message: 'Creating PDF dispute packet...'
    });

    // Real PDF generation
    setGenerationProgress({
      step: 'pdf',
      progress: 80,
      message: 'Adding identity documents...'
    });

    setGenerationProgress({
      step: 'pdf',
      progress: 100,
      message: 'Finalizing dispute packet...'
    });

    // In a real implementation, you would use jsPDF or similar:
    const pdf = new jsPDF();
    
    letters.forEach((letter, index) => {
      if (index > 0) pdf.addPage();
      
      // Add letter content to PDF
      const lines = pdf.splitTextToSize(letter.letterContent, 180);
      pdf.text(lines, 20, 20);
    });
    
    return pdf.output('blob');
  };

  // (Removed unused handleDocumentUpload function)

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

    setIsGenerating(true);

    try {
      // Step 1: Generate dispute letters
      const letters = await generateDisputeLetters();
      setGeneratedLetters(letters);

      // Step 2: Create PDF packet
      const pdfBlob = await generatePDFPacket(letters);

      // Step 3: Download the packet
      const filename = `dispute-packet-${new Date().toISOString().split('T')[0]}.pdf`;
      const url = URL.createObjectURL(pdfBlob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);

      // Step 4: Save generation record to database
      if (user?.id) {
        const { error: saveError } = await supabase
          .from('dispute_letter')
          .insert({
            id: `packet-${Date.now()}`,
            user_id: user.id,
            first_name: userProfile?.firstName,
            last_name: userProfile?.lastName,
            email: user.email || '',
            address: userProfile?.address1,
            city: userProfile?.city,
            state: userProfile?.state,
            zip: userProfile?.zipCode,
            tradelines: JSON.stringify(letters.map(l => ({
              creditor: l.creditorName,
              account: l.accountNumber,
              reason: l.disputeReason
            }))),
            created_on: new Date().toISOString()
          });

        if (saveError) {
          console.error('Error saving dispute record:', saveError);
        }
      }

      toast.success(`Dispute packet generated! ${letters.length} letters created and downloaded as ${filename}`);

    } catch (error) {
      console.error('Error generating dispute packet:', error);
      toast.error("Failed to generate dispute packet. Please try again.");
    } finally {
      setIsGenerating(false);
      setGenerationProgress({ step: '', progress: 0, message: '' });
    }
  };

  // Toggle tradeline selection
  const toggleTradelineSelection = (tradelineId: string) => {
    setSelectedTradelines(prev => 
      prev.includes(tradelineId) 
        ? prev.filter(id => id !== tradelineId)
        : [...prev, tradelineId]
    );
  };

  const isReadyToGenerate = userProfile && selectedTradelines.length > 0;

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
                        Go to Profile
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
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                  <div><strong>Name:</strong> {userProfile.firstName} {userProfile.lastName}</div>
                  <div><strong>Address:</strong> {userProfile.address1}</div>
                  <div><strong>Address2:</strong> {userProfile.address2}</div>
                  <div><strong>City:</strong> {userProfile.city}, {userProfile.state} {userProfile.zipCode}</div>
                  <div><strong>Phone Number:</strong> {userProfile.phoneNumber || 'Not provided'}</div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Negative Tradelines Selection */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Negative Tradelines to Dispute</CardTitle>
              <p className="text-sm text-muted-foreground">
                Select the negative accounts you want to dispute ({selectedTradelines.length} of {negativeTradelines.length} selected)
              </p>
            </CardHeader>
            <CardContent>
              {negativeTradelines.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <AlertCircle className="h-12 w-12 mx-auto mb-4" />
                  <p>No negative tradelines found.</p>
                  <Button 
                    variant="link" 
                    onClick={() => navigate('/upload')}
                    className="mt-2"
                  >
                    Upload credit report to find negative accounts
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
                      Select All
                    </Button>
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={() => setSelectedTradelines([])}
                    >
                      Select None
                    </Button>
                  </div>

                  {negativeTradelines.map((tradeline) => (
                    <div 
                      key={tradeline.id}
                      className={`
                        border rounded-lg p-4 cursor-pointer transition-colors
                        ${selectedTradelines.includes(tradeline.id) 
                          ? 'border-primary bg-primary/5' 
                          : 'border-muted hover:border-primary/50'
                        }
                      `}
                      onClick={() => toggleTradelineSelection(tradeline.id)}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <input
                              type="checkbox"
                              checked={selectedTradelines.includes(tradeline.id)}
                              onChange={() => toggleTradelineSelection(tradeline.id)}
                              className="rounded"
                            />
                            <h4 className="font-medium">{tradeline.creditor_name}</h4>
                            <Badge variant="destructive">Negative</Badge>
                          </div>
                          
                          <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-sm text-muted-foreground">
                            <div><strong>Account:</strong> {tradeline.account_number}</div>
                            <div><strong>Status:</strong> {tradeline.account_status}</div>
                            <div><strong>Balance:</strong> {tradeline.account_balance}</div>
                            <div><strong>Bureau:</strong> {tradeline.credit_bureau || 'Unknown'}</div>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Identity Documents */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Identity Documents (Optional)</CardTitle>
              <p className="text-sm text-muted-foreground">
                Add identity documents to strengthen your dispute letters
              </p>
            </CardHeader>
            <CardContent>
              {!showDocsSection ? (
                <Button onClick={() => setShowDocsSection(true)}>
                  Add Identity Documents
                </Button>
              ) : (
                <div className="space-y-4">
                  <DocumentUploadSection 
                    onClose={() => setShowDocsSection(false)}
                  />
                  
                  {uploadedDocuments.length > 0 && (
                    <div className="space-y-2">
                      <h4 className="font-medium">Uploaded Documents ({uploadedDocuments.length})</h4>
                      {uploadedDocuments.map((doc) => (
                        <div key={doc.id} className="flex items-center justify-between p-2 border rounded">
                          <div className="flex items-center gap-2">
                            <FileText className="h-4 w-4" />
                            <span className="text-sm">{doc.name}</span>
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
            <Card>
              <CardContent className="p-4">
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="font-medium">Generating Dispute Packet...</span>
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
              className="min-w-[250px]"
            >
              {isGenerating ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                  Generating Letters...
                </>
              ) : (
                <>
                  <FileText className="h-4 w-4 mr-2" />
                  Generate Dispute Letters ({selectedTradelines.length})
                </>
              )}
            </Button>
          </div>

          {/* Preview Generated Letters */}
          {generatedLetters.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Generated Dispute Letters</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {generatedLetters.map((letter, index) => (
                    <div key={letter.id} className="border rounded-lg p-4">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="font-medium">Letter {index + 1}: {letter.creditorName}</h4>
                        <Badge variant="outline">{letter.creditBureau}</Badge>
                      </div>
                      <div className="text-sm text-muted-foreground mb-2">
                        Account: {letter.accountNumber} • Reason: {letter.disputeReason}
                      </div>
                      <details className="text-sm">
                        <summary className="cursor-pointer font-medium mb-2">View Letter Content</summary>
                        <pre className="whitespace-pre-wrap bg-muted p-3 rounded text-xs">
                          {letter.letterContent}
                        </pre>
                      </details>
                    </div>
                  ))}
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