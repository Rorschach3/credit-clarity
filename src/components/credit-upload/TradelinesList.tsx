import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { TradelineEditor } from "./TradelineEditor";
import { ParsedTradeline } from "@/utils/tradelineParser";

interface TradelinesListProps {
  tradelines: ParsedTradeline[];
  selectedTradelineIds: Set<string>;
  onUpdate: (id: string, updated: Partial<ParsedTradeline>) => void;
  onDelete: (id: string) => void;
  onSelect: (id: string) => void;
  onAddManual: () => void;
}

export const TradelinesList = ({
  tradelines,
  selectedTradelineIds,
  onUpdate,
  onDelete,
  onSelect,
  onAddManual,
}: TradelinesListProps) => {
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
            isSelected={selectedTradelineIds?.has(tradeline.id || "")}
            onUpdate={(updates) => {
              if (tradeline.id) {
                onUpdate(tradeline.id, updates);
              }
            }}
            onDelete={() => {
              if (tradeline.id) {
                onDelete(tradeline.id);
              }
            }}
            onSelect={() => {
              if (typeof onSelect !== "function") {
                console.warn("[TradelinesList] onSelect is not a function:", onSelect);
                return;
              }
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
