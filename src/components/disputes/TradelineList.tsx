
import React from "react";
import { ParsedTradeline } from "@/utils/tradelineParser";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

interface TradelineListProps {
  tradelines: ParsedTradeline[];
  selected: ParsedTradeline[];
  setSelected: (lines: ParsedTradeline[]) => void;
  onAddManual: () => void;
}

export const TradelineList: React.FC<TradelineListProps> = ({
  tradelines,
  selected,
  setSelected,
  onAddManual,
}) => {
  const toggleSelect = (t: ParsedTradeline) => {
    if (!t.is_negative) return;
    setSelected(
      selected.includes(t) ? selected.filter((x) => x !== t) : [...selected, t]
    );
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <Label className="block">Select Tradelines to Dispute</Label>
        <Button size="sm" variant="outline" onClick={onAddManual}>
          + Add Tradeline Manually
        </Button>
      </div>
      {tradelines.length === 0 ? (
        <p className="text-muted-foreground text-sm">No tradelines found.</p>
      ) : (
        tradelines.map((t, i) => (
          <div key={i} className="border p-4 rounded mb-3 space-y-2">
            <div><strong>{t.creditor_name}</strong></div>
            <div>Account #: {t.account_number}</div>
            <div>Status: {t.account_status} — Negative: {t.is_negative ? "Yes" : "No"}</div>
            <div>Balance: ${parseFloat(t.account_balance?.replace(/[$,]/g, '') || '0').toFixed(2)}</div>
            <div>Date Opened: {t.date_opened || "N/A"}</div>
            <Input
              placeholder="Reason for Dispute (optional)"
              onChange={(e) => {
                // Add dispute reason logic if needed
              }}
            />
            <Button
              variant={selected.includes(t) ? "destructive" : "default"}
              onClick={() => toggleSelect(t)}
              disabled={!t.is_negative && !selected.includes(t)}
            >
              {selected.includes(t)
                ? "Remove from Dispute"
                : !t.is_negative
                ? "Cannot Dispute"
                : "Add to Dispute"}
            </Button>
          </div>
        ))
      )}
    </div>
  );
};
