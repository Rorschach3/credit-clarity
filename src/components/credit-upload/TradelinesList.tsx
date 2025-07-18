import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ParsedTradeline } from "@/utils/tradelineParser";
import { EditableTradelineCard } from "./EditableTradelineCard";

interface TradelinesListProps {
  tradelines: ParsedTradeline[];
  onDelete: (id: string) => void;
  onSaveAll: () => void;
  onAddManual: () => void;
  onUpdate?: (id: string, updated: Partial<ParsedTradeline>) => void;
}

export const TradelinesList = ({
  tradelines,
  onDelete,
  onSaveAll,
  onAddManual,
  onUpdate,
}: TradelinesListProps) => {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Extracted Tradelines ({tradelines.length})</CardTitle>
          <div className="flex gap-2">
            <Button size="sm" variant="outline" onClick={onAddManual}>
              + Add Manually
            </Button>
            {tradelines.length > 0 && (
              <Button size="sm" onClick={onSaveAll}>
                Save All
              </Button>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {tradelines.length === 0 ? (
          <p className="text-muted-foreground text-sm">No tradelines found.</p>
        ) : (
          <div className="space-y-4">
            {tradelines.map((tradeline, index) => (
              <EditableTradelineCard
                key={tradeline.id || index}
                tradeline={tradeline}
                onUpdate={(updates) => {
                  if (tradeline.id && onUpdate) {
                    onUpdate(tradeline.id, updates);
                  }
                }}
                onDelete={() => {
                  if (tradeline.id) {
                    onDelete(tradeline.id);
                  }
                }}
              />
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
};
