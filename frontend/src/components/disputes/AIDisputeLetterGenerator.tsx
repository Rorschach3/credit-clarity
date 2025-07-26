import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { useToast } from "@/hooks/use-toast";
import { supabase } from "@/integrations/supabase/client";
import { Loader2, Download, Printer, Wand2 } from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ParsedTradeline } from "@/utils/tradelineParser";

interface PersonalInfo {
  firstName: string;
  lastName: string;
  address: string;
  address2?: string;
  city: string;
  state: string;
  zip: string;
  phone?: string;
  lastFourSSN?: string;
}

interface AIDisputeLetterGeneratorProps {
  personalInfo: PersonalInfo;
  selectedTradelines: ParsedTradeline[];
  onComplete?: () => void;
}

export function AIDisputeLetterGenerator({ 
  personalInfo, 
  selectedTradelines, 
  onComplete 
}: AIDisputeLetterGeneratorProps) {
  const [activeTab, setActiveTab] = useState('Experian');
  const [isGenerating, setIsGenerating] = useState(false);
  const [customInstructions, setCustomInstructions] = useState('');
  const [letters, setLetters] = useState<Record<string, string>>({});
  const { toast } = useToast();
  const availableBureaus = Array.from(new Set([
    ...selectedTradelines.map(t => t.credit_bureau).filter(Boolean),
    'Experian', 'TransUnion', 'Equifax' // Always include all three
  ])).filter(bureau => ['Experian', 'TransUnion', 'Equifax'].includes(bureau));

  const generateLetters = async () => {
    if (selectedTradelines.length === 0) {
      toast({
        title: "No Items Selected",
        description: "Please select at least one tradeline to dispute.",
        variant: "destructive"
      });
      return;
    }

    setIsGenerating(true);
    try {
      console.log('Calling generate-dispute-letter function...');
      
      const { data, error } = await supabase.functions.invoke('generate-dispute-letter', {
        body: {
          personalInfo,
          selectedTradelines,
          bureaus: availableBureaus,
          letterType: 'enhanced',
          customInstructions: customInstructions.trim() || undefined
        }
      });

      if (error) {
        console.error('Supabase function error:', error);
        throw error;
      }

      if (data?.success && data?.letters) {
        setLetters(data.letters);
        toast({
          title: "Letters Generated Successfully",
          description: `Generated ${Object.keys(data.letters).length} dispute letter(s) using AI.`
        });
      } else {
        throw new Error('Failed to generate letters - invalid response');
      }

    } catch (error) {
      console.error('Error generating dispute letters:', error);
      toast({
        title: "Generation Failed",
        description: "Failed to generate dispute letters. Please try again.",
        variant: "destructive"
      });
    } finally {
      setIsGenerating(false);
    }
  };

  const downloadLetter = (bureau: string) => {
    const letter = letters[bureau];
    if (!letter) return;

    const blob = new Blob([letter], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `dispute-letter-${bureau.toLowerCase()}-${new Date().toISOString().split('T')[0]}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const printLetter = (bureau: string) => {
    const letter = letters[bureau];
    if (!letter) return;

    const printWindow = window.open('', '_blank');
    if (printWindow) {
      printWindow.document.write(`
        <html>
          <head>
            <title>Dispute Letter - ${bureau}</title>
            <style>
              body { 
                font-family: Arial, sans-serif; 
                line-height: 1.6; 
                margin: 1in;
                white-space: pre-wrap;
              }
            </style>
          </head>
          <body>${letter}</body>
        </html>
      `);
      printWindow.document.close();
      printWindow.print();
    }
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Wand2 className="h-5 w-5" />
          AI-Powered Dispute Letter Generator
        </CardTitle>
        <CardDescription>
          Generate professional, FCRA-compliant dispute letters for {selectedTradelines.length} selected item(s)
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        
        {/* Custom Instructions */}
        <div className="space-y-2">
          <Label htmlFor="customInstructions">
            Custom Instructions (Optional)
          </Label>
          <Textarea
            id="customInstructions"
            placeholder="Add any specific instructions or details you want included in your dispute letters..."
            value={customInstructions}
            onChange={(e) => setCustomInstructions(e.target.value)}
            rows={3}
          />
        </div>

        {/* Generate Button */}
        <Button 
          onClick={generateLetters}
          disabled={isGenerating || selectedTradelines.length === 0}
          className="w-full"
        >
          {isGenerating ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Generating AI Letters...
            </>
          ) : (
            <>
              <Wand2 className="mr-2 h-4 w-4" />
              Generate Professional Dispute Letters
            </>
          )}
        </Button>

        {/* Generated Letters */}
        {Object.keys(letters).length > 0 && (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold">Generated Letters</h3>
            
            <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
              <TabsList className="grid w-full grid-cols-3">
                {availableBureaus.map(bureau => (
                  <TabsTrigger key={bureau} value={bureau}>
                    {bureau}
                  </TabsTrigger>
                ))}
              </TabsList>
              
              {availableBureaus.map(bureau => (
                <TabsContent key={bureau} value={bureau} className="space-y-4">
                  {letters[bureau] && (
                    <>
                      <div className="flex gap-2 mb-4">
                        <Button
                          onClick={() => downloadLetter(bureau)}
                          variant="outline"
                          size="sm"
                        >
                          <Download className="mr-2 h-4 w-4" />
                          Download
                        </Button>
                        <Button
                          onClick={() => printLetter(bureau)}
                          variant="outline"
                          size="sm"
                        >
                          <Printer className="mr-2 h-4 w-4" />
                          Print
                        </Button>
                      </div>
                      
                      <div className="border rounded-lg p-4 bg-muted/50">
                        <pre className="whitespace-pre-wrap text-sm font-mono">
                          {letters[bureau]}
                        </pre>
                      </div>
                    </>
                  )}
                </TabsContent>
              ))}
            </Tabs>
          </div>
        )}

        {onComplete && Object.keys(letters).length > 0 && (
          <Button onClick={onComplete} className="w-full">
            Complete & Save Letters
          </Button>
        )}
      </CardContent>
    </Card>
  );
}