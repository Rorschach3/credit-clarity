
import { Button } from "@/components/ui/button";
import { EnhancedDisputeLetterGenerator } from "@/components/disputes/EnhancedDisputeLetterGenerator";
import { NegativeItem } from "@/types/document";

interface GenerateLettersSectionProps {
  selectedItems: NegativeItem[];
  personalInfo: any;
  onComplete: () => void;
  onBackToDocuments: () => void;
  onBackToItems: () => void;
}

export function GenerateLettersSection({
  selectedItems,
  personalInfo,
  onComplete,
  onBackToDocuments,
  onBackToItems
}: GenerateLettersSectionProps) {
  return (
    <>
      <EnhancedDisputeLetterGenerator 
        items={selectedItems}
        onComplete={onComplete}
        personalInfo={personalInfo}
      />
      <div className="mt-4 flex gap-2">
        <Button 
          variant="outline" 
          onClick={onBackToDocuments}
        >
          Back to Documents
        </Button>
        <Button 
          variant="outline" 
          onClick={onBackToItems}
        >
          Back to Item Selection
        </Button>
      </div>
    </>
  );
}
