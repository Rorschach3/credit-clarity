import { useState } from "react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { type NegativeItem } from "@/types/negative-item";
import { useToast } from "@/hooks/use-toast";
import { supabase } from "@/integrations/supabase/client";
import { Loader2, Save, AlertCircle } from "lucide-react";
import { type Bureau, bureauAddresses } from "@/utils/bureau-constants";
import { BureauTabs } from "./BureauTabs";
import { useAuth } from "@/hooks/use-auth";
import type { PersonalInfo } from "./EnhancedDisputeLetterGenerator";

interface DisputeLetterGeneratorProps {
  items: NegativeItem[];
  onComplete: () => void;
  personalInfo?: PersonalInfo;
}

export function DisputeLetterGenerator({ items, onComplete, personalInfo }: DisputeLetterGeneratorProps) {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<Bureau>('Experian');
  const [isGenerating, setIsGenerating] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [letters, setLetters] = useState<Record<Bureau, string | null>>({
    'Experian': null,
    'TransUnion': null,
    'Equifax': null
  });
  const { toast } = useToast();

  // Profile completion check
  const missingFields: string[] = [];
  if (!personalInfo?.firstName || !personalInfo?.lastName) missingFields.push('Full name');
  if (!personalInfo?.address || !personalInfo?.city || !personalInfo?.state || !personalInfo?.zip) missingFields.push('Address');
  if (!personalInfo?.ssnLastFour) missingFields.push('SSN last 4 digits');
  const isProfileReady = missingFields.length === 0;

  const bureaus = Array.from(new Set(
    items.flatMap(item => item.bureaus)
  )).filter(bureau =>
    bureau === 'Experian' || bureau === 'TransUnion' || bureau === 'Equifax'
  ) as Bureau[];

  const generateLetter = (bureau: Bureau) => {
    if (!isProfileReady) return;
    setIsGenerating(true);

    const bureauItems = items.filter(item => item.bureaus.includes(bureau));

    const currentDate = new Date().toLocaleDateString('en-US', {
      month: 'long',
      day: 'numeric',
      year: 'numeric'
    });

    const fullName = `${personalInfo!.firstName} ${personalInfo!.lastName}`;
    const fullAddress = `${personalInfo!.address}\n${personalInfo!.city}, ${personalInfo!.state} ${personalInfo!.zip}`;

    const letterContent = `${currentDate}

${bureauAddresses[bureau]}

Re: Request for Investigation of Items on Credit Report

To Whom It May Concern:

I am writing to dispute the following information in my credit report. The items I dispute are marked by an "X" below.

${bureauItems.map((item, index) => `
X Item ${index + 1}: ${item.creditorName}
Account Number: ${item.accountNumber}
Reason for Dispute: This information is inaccurate because I do not recognize this account. Please investigate this matter and remove the inaccurate information from my credit report.
`).join('\n')}

Under the Fair Credit Reporting Act, you are required to investigate these disputes and provide me with the results of your investigation. If you cannot verify these items, they must be removed from my credit report.

Please send me notification of the results of your investigation.

Sincerely,

${fullName}
${fullAddress}
SSN (Last 4): XXX-XX-${personalInfo!.ssnLastFour?.replace(/\D/g, '').slice(-4) ?? 'XXXX'}
`;

    setLetters(prev => ({ ...prev, [bureau]: letterContent }));
    setIsGenerating(false);
  };

  const saveDisputes = async () => {
    setIsSaving(true);

    try {
      const promises = bureaus.map(async (bureau) => {
        const letter = letters[bureau];
        if (!letter) return null;

        const { data, error } = await supabase
          .from('disputes')
          .insert({
            credit_report_id: `dispute-${Date.now()}`,
            mailing_address: bureauAddresses[bureau],
            status: 'pending',
            user_id: user?.id ?? null
          })
          .select();

        if (error) throw error;
        return data;
      });

      await Promise.all(promises);

      toast({
        title: "Disputes Saved",
        description: "Your dispute letters have been saved successfully.",
      });

      onComplete();
    } catch (error) {
      console.error("Error saving disputes:", error);
      toast({
        title: "Error",
        description: "There was an error saving your dispute letters.",
        variant: "destructive"
      });
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <Card className="w-full mt-6">
      <CardHeader>
        <CardTitle>Dispute Letters</CardTitle>
        <CardDescription>
          Review and customize your dispute letters for each credit bureau
        </CardDescription>
      </CardHeader>
      <CardContent>
        {/* Profile completion gate */}
        {!isProfileReady && (
          <div className="flex items-start gap-3 rounded-lg border border-amber-500/30 bg-amber-500/10 p-4 mb-5">
            <AlertCircle className="h-5 w-5 text-amber-400 mt-0.5 flex-shrink-0" />
            <div className="text-sm">
              <p className="font-semibold text-amber-300 mb-1">Profile incomplete — cannot generate letters</p>
              <p className="text-amber-200/80 mb-2">
                The following required fields are missing:{' '}
                <span className="font-medium">{missingFields.join(', ')}</span>.
              </p>
              <p className="text-amber-200/70 text-xs mb-3">
                Your name, address, and SSN last 4 digits must be on file so the bureau can verify your identity.
              </p>
              <Link to="/profile">
                <Button size="sm" className="btn-gold rounded-md h-8 px-4 text-xs">
                  Complete Profile
                </Button>
              </Link>
            </div>
          </div>
        )}

        {bureaus.length === 0 ? (
          <div className="text-center p-6">
            <p className="text-muted-foreground">
              No credit bureaus to dispute with. Please select items that have bureau reporting.
            </p>
          </div>
        ) : (
          <>
            <div className="flex justify-between items-center mb-4">
              <Button
                onClick={saveDisputes}
                disabled={isSaving || bureaus.some(bureau => !letters[bureau]) || !isProfileReady}
              >
                {isSaving ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Saving
                  </>
                ) : (
                  <>
                    <Save className="mr-2 h-4 w-4" />
                    Save Dispute Letters
                  </>
                )}
              </Button>
            </div>

            <BureauTabs
              activeTab={activeTab}
              setActiveTab={setActiveTab}
              bureaus={bureaus}
              letters={letters}
              isGenerating={isGenerating}
              onGenerateLetter={isProfileReady ? generateLetter : () => {}}
            />
          </>
        )}
      </CardContent>
    </Card>
  );
}
