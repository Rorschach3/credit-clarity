import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
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

const BUREAUS = [
  { key: 'equifax',    label: 'Equifax',    headerClass: 'bg-red-600',   colClass: 'border-red-200 dark:border-red-800' },
  { key: 'experian',   label: 'Experian',   headerClass: 'bg-blue-700',  colClass: 'border-blue-200 dark:border-blue-800' },
  { key: 'transunion', label: 'TransUnion', headerClass: 'bg-green-700', colClass: 'border-green-200 dark:border-green-800' },
] as const;

export const TradelinesList = ({
  tradelines,
  onUpdate,
  onDelete,
  onAddManual,
  savingTradelines = new Set(),
  saveErrors = new Set(),
}: TradelinesListProps) => {
  const grouped = BUREAUS.reduce<Record<string, ParsedTradeline[]>>((acc, b) => {
    acc[b.key] = tradelines.filter(t => t.credit_bureau?.toLowerCase() === b.key);
    return acc;
  }, {} as Record<string, ParsedTradeline[]>);

  const unassigned = tradelines.filter(
    t => !t.credit_bureau || !BUREAUS.some(b => b.key === t.credit_bureau?.toLowerCase())
  );

  const makeEditors = (list: ParsedTradeline[]) =>
    list.map((tradeline, index) => (
      <TradelineEditor
        key={tradeline.id || index}
        tradeline={tradeline}
        index={index}
        onUpdate={onUpdate ? (updates) => {
          if (tradeline.id) onUpdate(tradeline.id, updates);
        } : () => {}}
        onDelete={() => {
          if (tradeline.id) onDelete(tradeline.id);
        }}
        isSaving={tradeline.id ? savingTradelines.has(tradeline.id) : false}
        hasError={tradeline.id ? saveErrors.has(tradeline.id) : false}
      />
    ));

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <Label className="block">
          Tradelines ({tradelines.length}) — Auto-save enabled
        </Label>
        <Button size="sm" variant="outline" onClick={onAddManual}>
          + Add Manually
        </Button>
      </div>

      {tradelines.length === 0 ? (
        <p className="text-muted-foreground text-sm">No tradelines found.</p>
      ) : (
        <>
          {/* Three-bureau columns */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {BUREAUS.map(bureau => (
              <div key={bureau.key} className={`rounded-lg border ${bureau.colClass} overflow-hidden`}>
                <div className={`${bureau.headerClass} px-4 py-2 flex items-center justify-between`}>
                  <span className="font-semibold text-white text-sm">{bureau.label}</span>
                  <Badge variant="secondary" className="text-xs bg-white/20 text-white border-0">
                    {grouped[bureau.key].length}
                  </Badge>
                </div>
                <div className="p-3 space-y-3 min-h-[80px]">
                  {grouped[bureau.key].length === 0 ? (
                    <p className="text-muted-foreground text-xs text-center py-4">
                      No tradelines for this bureau
                    </p>
                  ) : (
                    makeEditors(grouped[bureau.key])
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* Unassigned tradelines */}
          {unassigned.length > 0 && (
            <div className="rounded-lg border border-dashed border-muted-foreground/30 overflow-hidden">
              <div className="bg-muted px-4 py-2 flex items-center justify-between">
                <span className="font-semibold text-sm text-muted-foreground">Unassigned Bureau</span>
                <Badge variant="outline" className="text-xs">{unassigned.length}</Badge>
              </div>
              <div className="p-3 space-y-3">
                {makeEditors(unassigned)}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default TradelinesList;
