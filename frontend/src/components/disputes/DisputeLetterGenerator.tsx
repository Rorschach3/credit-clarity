import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { type NegativeItem } from "@/types/document";
import { useToast } from "@/hooks/use-toast";
import { supabase } from "../../../supabase/client";
import { Tables } from "@/integrations/supabase/schema";
import { Loader2, Save } from "lucide-react";
import { type Bureau, bureauAddresses } from "@/utils/bureau-constants";
import { BureauTabs } from "./BureauTabs";

interface DisputeLetterGeneratorProps {
  items: NegativeItem[];
  onComplete: () => void;
}

// Temporary default user ID until authentication is implemented
const TEMP_USER_ID = '00000000-0000-0000-0000-000000000000';

export function DisputeLetterGenerator({ items, onComplete }: DisputeLetterGeneratorProps) {
  const [activeTab, setActiveTab] = useState<Bureau>('Experian');
  const [isGenerating, setIsGenerating] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [letters, setLetters] = useState<Record<Bureau, string | null>>({
    'Experian': null,
    'TransUnion': null,
    'Equifax': null
  });
  const { toast } = useToast();

  // Get all bureaus represented in the selected items
  const bureaus = Array.from(new Set(
    items.flatMap(item => item.bureaus)
  )).filter(bureau => 
    bureau === 'Experian' || bureau === 'TransUnion' || bureau === 'Equifax'
  ) as Bureau[];

  const generateLetter = (bureau: Bureau) => {
    setIsGenerating(true);
    
    // Items to dispute for this bureau
    const bureauItems = items.filter(item => item.bureaus.includes(bureau));
    
    // Generate the letter content
    const currentDate = new Date().toLocaleDateString('en-US', {
      month: 'long',
      day: 'numeric',
      year: 'numeric'
    });

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

[Your Name]
[Your Address]
[Your City, State, ZIP]
[Your Social Security Number]
`;

    setLetters(prev => ({
      ...prev,
      [bureau]: letterContent
    }));
    
    setIsGenerating(false);
  };

  const saveDisputes = async () => {
    setIsSaving(true);
    
    try {
      const promises = bureaus.map(async (bureau) => {
        const letter = letters[bureau];
        if (!letter) return null;
        
        const { data, error } = await supabase
          .from(Tables.disputes)
          .insert({
            credit_bureau: bureau,
            mailing_address: bureauAddresses[bureau],
            letter_content: letter,
            status: 'pending',
            user_id: TEMP_USER_ID
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
              onGenerateLetter={generateLetter}
            />
          </>
        )}
      </CardContent>
    </Card>
  );
}
