
import { Button } from "@/components/ui/button";

interface ListActionsProps {
  selectedCount: number;
  totalCount: number;
  onGenerateDisputes: () => void;
}

export function ListActions({ 
  selectedCount, 
  totalCount, 
  onGenerateDisputes 
}: ListActionsProps) {
  return (
    <div className="flex justify-between items-center mt-6 pt-4 border-t">
      <p className="text-sm text-muted-foreground">
        {selectedCount} of {totalCount} items selected
      </p>
      <Button 
        onClick={onGenerateDisputes}
        disabled={selectedCount === 0}
      >
        Generate Dispute Letters
      </Button>
    </div>
  );
}
