
import React from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Eye, Loader2 } from "lucide-react";
import { type Bureau } from "@/utils/bureau-constants";
import { DisputeLetterPreview } from "./DisputeLetterPreview";

interface BureauTabsProps {
  activeTab: Bureau;
  setActiveTab: (bureau: Bureau) => void;
  bureaus: Bureau[];
  letters: Record<Bureau, string | null>;
  isGenerating: boolean;
  onGenerateLetter: (bureau: Bureau) => void;
}

export function BureauTabs({
  activeTab,
  setActiveTab,
  bureaus,
  letters,
  isGenerating,
  onGenerateLetter,
}: BureauTabsProps) {
  return (
    <Tabs defaultValue={bureaus[0]} value={activeTab} onValueChange={(value) => setActiveTab(value as Bureau)}>
      <TabsList className="w-full">
        {bureaus.map(bureau => (
          <TabsTrigger 
            key={bureau} 
            value={bureau}
            className="flex-1"
          >
            {bureau}
          </TabsTrigger>
        ))}
      </TabsList>
      
      {bureaus.map(bureau => (
        <TabsContent key={bureau} value={bureau} className="mt-4">
          {!letters[bureau] ? (
            <div className="flex flex-col items-center justify-center p-8 border rounded-md">
              <p className="text-center text-muted-foreground mb-4">
                Generate a dispute letter for {bureau} based on the selected items
              </p>
              <Button 
                onClick={() => onGenerateLetter(bureau)}
                disabled={isGenerating}
              >
                {isGenerating ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Generating
                  </>
                ) : (
                  <>
                    <Eye className="mr-2 h-4 w-4" />
                    Generate Letter
                  </>
                )}
              </Button>
            </div>
          ) : (
            <DisputeLetterPreview letterContent={letters[bureau]!} />
          )}
        </TabsContent>
      ))}
    </Tabs>
  );
}

