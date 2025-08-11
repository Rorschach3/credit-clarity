import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { TradelineEditor } from "./TradelineEditor";
import { ParsedTradeline } from "@/utils/tradelineParser";

interface TradelinesListProps {
  tradelines: ParsedTradeline[];
  onUpdate?: (id: string, updated: Partial<ParsedTradeline>) => void;
  onDelete: (id: string) => void;
  onAddManual: () => void;
  savingTradelines?: Set<string>;
  saveErrors?: Set<string>;
}

export const TradelinesList = ({
  tradelines,
  onUpdate,
  onDelete,
  onAddManual,
  savingTradelines = new Set(),
  saveErrors = new Set(),
}: TradelinesListProps) => {
  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <Label className="block">Tradelines ({tradelines.length}) - Auto-save enabled</Label>
        <Button size="sm" variant="outline" onClick={onAddManual}>
          + Add Manually
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
            onUpdate={onUpdate ? (updates) => {
              if (tradeline.id) {
                onUpdate(tradeline.id, updates);
              }
            } : () => {}}
            onDelete={() => {
              if (tradeline.id) {
                onDelete(tradeline.id);
              }
            }}
            isSaving={tradeline.id ? savingTradelines.has(tradeline.id) : false}
            hasError={tradeline.id ? saveErrors.has(tradeline.id) : false}
          />
        ))
      )}
    </div>
  );
};

export default TradelinesList;