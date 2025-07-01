
import React from 'react';
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { TradelineEditor } from './TradelineEditor';
import { ParsedTradeline } from "@/utils/tradelineParser";

interface TradelinesListProps {
  tradelines: ParsedTradeline[];
  selectedTradelineIds: Set<string>;
  onUpdate: (index: number, updated: Partial<ParsedTradeline>) => void;
  onDelete: (index: number) => void;
  onSelect: (id: string, selected: boolean) => void;
  onAddManual: () => void;
}

export const TradelinesList: React.FC<TradelinesListProps> = ({
  tradelines,
  selectedTradelineIds,
  onUpdate,
  onDelete,
  onSelect,
  onAddManual
}) => {
  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <Label className="block">Tradelines</Label>
        <Button size="sm" variant="outline" onClick={onAddManual}>
          + Add Tradeline Manually
        </Button>
      </div>
      {tradelines.length === 0 ? (
        <p className="text-muted-foreground text-sm">No tradelines found.</p>
      ) : (
        tradelines.map((tradeline, index) => (
          <TradelineEditor
            key={tradeline.id || index}
            tradeline={tradeline}
            index={index}
            isSelected={selectedTradelineIds.has(tradeline.id || '')}
            onUpdate={onUpdate}
            onDelete={onDelete}
            onSelect={onSelect}
          />
        ))
      )}
    </div>
  );
};
