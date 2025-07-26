
import React from 'react';
import { Button } from "@/components/ui/button";
import { useNavigate } from "react-router-dom";

interface UploadActionsProps {
  selectedTradelineIds: Set<string>;
  tradelines: any[];
}

export const UploadActions: React.FC<UploadActionsProps> = ({
  selectedTradelineIds,
  tradelines
}) => {
  const navigate = useNavigate();

  const handleProceed = () => {
    const selectedTradelines = tradelines.filter(t => selectedTradelineIds.has(t.id || ''));
    console.log("Proceeding with selected tradelines:", selectedTradelines);
    
    if (selectedTradelines.length === 0) {
      return;
    }
    
    navigate("/dispute-letter", {
      state: {
        selectedTradelineIds: Array.from(selectedTradelineIds),
        selectedTradelines: selectedTradelines
      }
    });
  };

  return (
    <div className="flex justify-end space-x-4">
      <Button 
        onClick={handleProceed} 
        disabled={selectedTradelineIds.size === 0}
        className="min-w-[200px]"
      >
        Generate Dispute Letters ({selectedTradelineIds.size} selected)
      </Button>
    </div>
  );
};
