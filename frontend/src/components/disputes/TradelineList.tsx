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
    if (!t.isNegative) return;
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
            <div><strong>{t.creditorName}</strong></div>
            <div>Account #: {t.accountNumber}</div>
            <div>Status: {t.status} — Negative: {t.isNegative ? "Yes" : "No"}</div>
            {t.negativeReason && <div>Reason: {t.negativeReason}</div>}
            <div>Balance: ${t.balance && Number(t.balance).toFixed(2) || "0.00"}</div>
            <div>Date Opened: {t.dateOpened || "N/A"}</div>
            <Input
              placeholder="Reason for Dispute (optional)"
              defaultValue={t.negativeReason}
              onChange={(e) => {
                if (e.target.value.length < 200) {
                  t.negativeReason = e.target.value;
                } else {
                  alert("Reason for dispute cannot exceed 200 characters.");
                  e.target.value = t.negativeReason || "";
                }
              }}
            />
            <Button
              variant={selected.includes(t) ? "destructive" : "default"}
              onClick={() => toggleSelect(t)}
              disabled={!t.isNegative && !selected.includes(t)}
            >
              {selected.includes(t)
                ? "Remove from Dispute"
                : !t.isNegative
                ? "Cannot Dispute"
                : "Add to Dispute"}
            </Button>
          </div>
        ))
      )}
    </div>
  );
};
