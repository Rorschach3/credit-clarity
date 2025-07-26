import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import type { NegativeItem } from "@/types/document";
import { useToast } from "@/hooks/use-toast";
import { supabase } from "../../../supabase/client";
import { Loader2, Save, Bot, CheckCircle, RefreshCw, AlertCircle } from "lucide-react";
import { type Bureau, bureauAddresses } from "@/utils/bureau-constants";
import { Progress } from "@/components/ui/progress";
import { aiService } from "@/utils/ai-service";
import { DisputeLetterPreview } from "./DisputeLetterPreview";
import { useAuth } from "@/hooks/use-auth";

interface EnhancedDisputeLetterGeneratorProps {
  items: NegativeItem[];
  onComplete: () => void;
  personalInfo?: Record<string, string | undefined>;
}

// Temporary default user ID until authentication is implemented
const TEMP_USER_ID = '00000000-0000-0000-0000-000000000000';

type LetterState = Record<Bureau, string | null>;
type QualityState = Record<Bureau, number>;
type SuggestionsState = Record<Bureau, string[]>;

export function EnhancedDisputeLetterGenerator({
  items,
  onComplete,
  personalInfo: propPersonalInfo
}: EnhancedDisputeLetterGeneratorProps) {
  const [activeTab, setActiveTab] = useState<Bureau>('Experian');
  const [isGenerating, setIsGenerating] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isReviewing, setIsReviewing] = useState(false);
  const [letters, setLetters] = useState<LetterState>({
    'Experian': null,
    'TransUnion': null,
    'Equifax': null
  });
  const [letterQuality, setLetterQuality] = useState<QualityState>({
    'Experian': 0,
    'TransUnion': 0,
    'Equifax': 0
  });
  const [letterSuggestions, setLetterSuggestions] = useState<SuggestionsState>({
    'Experian': [],
    'TransUnion': [],
    'Equifax': []
  });
  const [generationProgress, setGenerationProgress] = useState(0);
  const [personalInfo, setPersonalInfo] = useState<Record<string, string | undefined> | undefined>(propPersonalInfo);
  const { toast } = useToast();
  const { user } = useAuth();

  // Get all bureaus represented in the selected items
  const bureaus = Array.from(new Set(
    items.flatMap(item => item.bureaus)
  )).filter(bureau =>
    bureau === 'Experian' || bureau === 'TransUnion' || bureau === 'Equifax'
  ) as Bureau[];

  // Use provided personal info or fetch from database
  useEffect(() => {
    if (propPersonalInfo) {
      setPersonalInfo(propPersonalInfo);
      return;
    }

    type Profile = {
      firstName: string;
      lastName: string;
      address: string;
      city: string;
      state: string;
      zip: string;
      phone?: string;
      email: string;
      ssnLastFour?: string;
    };
    const fetchPersonalInfo = async () => {
      if (!user) return;

      try {
        const { data, error } = await supabase
          .from("profiles")
          .select("firstName, lastName, address, city, state, zip, phone, email, ssnLastFour")
          .eq('id', 'ac9f2b0d-d10c-4124-b03c-56215faeb6a6')
          .single<Profile>();

        if (error) {
          console.error("Error fetching personal info:", error);
          return;
        }

        if (data) {
          const { firstName, lastName, address, city, state, zip, phone, email, ssnLastFour } = data;

          setPersonalInfo({
            firstName: firstName,
            lastName: lastName,
            address: address,
            city: city,
            state: state,
            zip: zip,
            phone: phone || undefined,
            email: email,
            ssnLastFour: ssnLastFour || undefined
          });
        }
      } catch (error) {
        console.error("Error in fetching personal info:", error);
      }
    };

    fetchPersonalInfo();
  }, [user, propPersonalInfo]);

  const generateFallbackLetter = (bureauItems: NegativeItem[], bureau: Bureau): string => {
    const currentDate = new Date().toLocaleDateString('en-US', {
      month: 'long',
      day: 'numeric',
      year: 'numeric'
    });

    const userInfo = personalInfo || {};

    const firstName = userInfo.firstName || '[YOUR FIRST NAME]';
    const lastName = userInfo.lastName || '[YOUR LAST NAME]';
    const address = userInfo.address || '[YOUR ADDRESS]';
    const city = userInfo.city || '[YOUR CITY]';
    const state = userInfo.state || '[YOUR STATE]';
    const zip = userInfo.zip || '[YOUR ZIP]';
    const ssnLastFour = userInfo.ssnLastFour || '[LAST 4 SSN DIGITS]';

    const fullAddress = `${address}, ${city}, ${state} ${zip}`;

    return `${currentDate}

${firstName} ${lastName}
${address}
${city}, ${state} ${zip}

${bureauAddresses[bureau]}

Re: Request for Investigation of Items on Credit Report

To Whom It May Concern:

I am writing to dispute the following information in my credit report. The items I dispute are marked by an "X" below.

${bureauItems.map((item, index) => `
X Item ${index + 1}: ${item.creditorName}
Account Number: ${item.accountNumber}
Reason for Dispute: This information is inaccurate because I do not recognize this account. Please investigate this matter and remove the inaccurate information from my credit report.
`).join('\n')}

Under the Fair Credit Reporting Act, Section 611, you are required to investigate these disputes and provide me with the results of your investigation within 30 days. If you cannot verify these items, they must be removed from my credit report.

I am including copies of my government-issued ID, Social Security card, and a recent utility bill to verify my identity as required.

Please send me notification of the results of your investigation.

Sincerely,

${firstName} ${lastName}`;
  };

  const generateLetter = async (bureau: Bureau) => {
    setIsGenerating(true);
    setGenerationProgress(10);

    try {
      // Items to dispute for this bureau
      const bureauItems = items.filter(item => item.bureaus.includes(bureau));
      setGenerationProgress(30);

      try {
        // Generate the letter content using AI
        const generatedLetter = await aiService.generateDisputeLetter(bureauItems, bureau, personalInfo);
        setGenerationProgress(70);

        // Update state with the generated letter
        setLetters(prev => ({ ...prev, [bureau]: generatedLetter.content }));
        setLetterQuality(prev => ({ ...prev, [bureau]: generatedLetter.qualityScore }));
        setLetterSuggestions(prev => ({ ...prev, [bureau]: generatedLetter.suggestions }));
      } catch (error) {
        console.error("AI letter generation failed, using fallback:", error);

        // Fallback to template if AI fails
        const fallbackLetter = generateFallbackLetter(bureauItems, bureau);

        setLetters(prev => ({ ...prev, [bureau]: fallbackLetter }));
        setLetterQuality(prev => ({ ...prev, [bureau]: 75 }));
        setLetterSuggestions(prev => ({
          ...prev,
          [bureau]: ["Consider adding more specific dispute reasons"]
        }));

        toast({
          title: "AI Generation Unavailable",
          description: "Using template letter instead. You can edit it as needed.",
          variant: "default"
        });
      }

      setGenerationProgress(100);
      toast({
        title: "Letter Generated",
        description: `Dispute letter for ${bureau} has been created successfully.`,
      });
    } catch (error) {
      console.error("Error generating letter:", error);
      toast({
        title: "Generation Failed",
        description: "There was an error creating your dispute letter. Please try again.",
        variant: "destructive"
      });
    } finally {
      setIsGenerating(false);
    }
  };

  const reviewLetter = async (bureau: Bureau) => {
    if (!letters[bureau]) return;

    setIsReviewing(true);

    try {
      try {
        const reviewedLetter = await aiService.reviewDisputeLetter(letters[bureau]!, bureau);

        setLetters(prev => ({ ...prev, [bureau]: reviewedLetter.content }));
        setLetterQuality(prev => ({ ...prev, [bureau]: reviewedLetter.qualityScore }));
        setLetterSuggestions(prev => ({ ...prev, [bureau]: reviewedLetter.suggestions }));
      } catch (error) {
        console.error("AI letter review failed:", error);
        toast({
          title: "Review Failed",
          description: "AI review unavailable. You can still edit the letter manually.",
          variant: "default"
        });
      }

      toast({
        title: "Letter Review Complete",
        description: "Your dispute letter has been reviewed and optimized.",
      });
    } catch (error) {
      console.error("Error reviewing letter:", error);
      toast({
        title: "Review Failed",
        description: "There was an error reviewing your dispute letter.",
        variant: "destructive"
      });
    } finally {
      setIsReviewing(false);
    }
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
            credit_bureau: bureau,
            mailing_address: bureauAddresses[bureau],
            letter_content: letter,
            status: 'pending',
            user_id: user?.id || TEMP_USER_ID
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

  const getQualityColor = (score: number) => {
    if (score >= 90) return 'text-green-700 bg-green-100';
    if (score >= 75) return 'text-yellow-700 bg-yellow-100';
    return 'text-red-700 bg-red-100';
  };

  const renderLetterContent = (bureau: Bureau) => {
    if (!letters[bureau]) {
      return (
        <div className="text-center py-8">
          {isGenerating && activeTab === bureau ? (
            <div className="space-y-4">
              <Loader2 className="h-8 w-8 animate-spin mx-auto text-primary" />
              <div>
                <p className="font-medium">Generating your dispute letter</p>
                <p className="text-sm text-muted-foreground">
                  Creating a personalized letter for {bureau}
                </p>
              </div>
              <Progress value={generationProgress} className="w-64 mx-auto" />
            </div>
          ) : (
            <>
              <Button onClick={() => generateLetter(bureau)}>
                <Bot className="mr-2 h-4 w-4" />
                Generate {bureau} Letter
              </Button>
              <p className="mt-2 text-sm text-muted-foreground">
                Click to create an optimized dispute letter
              </p>
            </>
          )}
        </div>
      );
    }

    return (
      <div className="space-y-4">
        {letterQuality[bureau] > 0 && (
          <div className="flex items-center gap-2 mb-3">
            <div className={`px-2 py-1 rounded text-xs font-medium flex items-center ${getQualityColor(letterQuality[bureau])}`}>
              {letterQuality[bureau] >= 90 ? (
                <CheckCircle className="h-3 w-3 mr-1" />
              ) : (
                <AlertCircle className="h-3 w-3 mr-1" />
              )}
              Quality Score: {letterQuality[bureau]}%
            </div>

            <Button
              variant="outline"
              size="sm"
              className="text-xs h-7 px-2"
              onClick={() => reviewLetter(bureau)}
              disabled={isReviewing}
            >
              {isReviewing ? (
                <Loader2 className="h-3 w-3 mr-1 animate-spin" />
              ) : (
                <RefreshCw className="h-3 w-3 mr-1" />
              )}
              Review & Improve
            </Button>
          </div>
        )}

        {letterSuggestions[bureau]?.length > 0 && (
          <Alert className="bg-yellow-50 border-yellow-200 mb-3">
            <div className="flex flex-col gap-1">
              <p className="font-medium text-yellow-800">AI Suggestions:</p>
              <ul className="text-sm list-disc pl-5">
                {letterSuggestions[bureau].map((suggestion, idx) => (
                  <li key={idx} className="text-yellow-800">{suggestion}</li>
                ))}
              </ul>
            </div>
          </Alert>
        )}

        <DisputeLetterPreview
          letterContent={letters[bureau]!}
          bureau={bureau}
        />
      </div>
    );
  };

  return (
    <Card className="w-full mt-6">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              AI-Enhanced Dispute Letters
              <Badge variant="outline" className="bg-blue-100 text-blue-800 ml-2">AI Powered</Badge>
            </CardTitle>
            <CardDescription>
              Review and customize your dispute letters for each credit bureau
            </CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent>
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
                disabled={isSaving || bureaus.some(bureau => !letters[bureau])}
              >
                {isSaving ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Saving
                  </>
                ) : (
                  <>
                    <Save className="mr-2 h-4 w-4" />
                    Save All Dispute Letters
                  </>
                )}
              </Button>
            </div>

            {!personalInfo && (
              <Alert variant="default" className="mb-4 bg-amber-50 border-amber-200 text-amber-800">
                <AlertDescription>
                  We're using default personal information in your letter. For a more personalized letter,
                  please go back and complete your personal information.
                </AlertDescription>
              </Alert>
            )}

            <Tabs value={activeTab} onValueChange={(value) => setActiveTab(value as Bureau)} className="w-full">
              <TabsList className="grid" style={{ gridTemplateColumns: `repeat(${bureaus.length}, 1fr)` }}>
                {bureaus.map(bureau => (
                  <TabsTrigger key={bureau} value={bureau} className="flex items-center gap-1">
                    {bureau}
                    {letterQuality[bureau] > 0 && (
                      <span className={`ml-2 ${getQualityColor(letterQuality[bureau])}`}>
                        {letterQuality[bureau]}%
                      </span>
                    )}
                  </TabsTrigger>
                ))}
              </TabsList>

              {bureaus.map(bureau => (
                <TabsContent key={bureau} value={bureau} className="space-y-4">
                  {renderLetterContent(bureau)}
                </TabsContent>
              ))}
            </Tabs>
          </>
        )}
      </CardContent>
    </Card>
  );
}
