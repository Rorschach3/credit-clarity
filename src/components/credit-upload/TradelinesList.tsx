import React from 'react';
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { TradelineEditor } from './TradelineEditor';
import { ParsedTradeline } from "@/utils/tradelineParser";

interface TradelinesListProps {
  tradelines: ParsedTradeline[];
  selectedTradelineIds: Set<string>;
  onUpdate: (id: string, updated: Partial<ParsedTradeline>) => void; // ✅ Changed from index to id
  onDelete: (id: string) => void; // ✅ Changed from index to id
  onSelect: (id: string) => void; // ✅ Simplified - removed selected boolean
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
            index={index} // Keep index for TradelineEditor if it needs it
            isSelected={selectedTradelineIds.has(tradeline.id || '')}
            onUpdate={(updates: Partial<ParsedTradeline>) => {
              // ✅ Convert index-based call to ID-based call
              if (tradeline.id) {
                onUpdate(tradeline.id, updates);
              }
            }}
            onDelete={() => {
              // ✅ Convert index-based call to ID-based call
              if (tradeline.id) {
                onDelete(tradeline.id);
              }
            }}
            onSelect={(selected: boolean) => {
              // ✅ Convert to simple ID-based call (hook handles toggle logic)
              if (tradeline.id) {
                onSelect(tradeline.id);
              }
            }}
          />
        ))
      )}
    </div>
  );
};