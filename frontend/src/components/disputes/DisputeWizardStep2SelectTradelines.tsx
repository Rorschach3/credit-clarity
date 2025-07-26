import React, { useState, useEffect } from "react";
import { ParsedTradeline } from "@/utils/tradelineParser";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

interface DisputeWizardStep2SelectTradelinesProps {
  tradelines: ParsedTradeline[];
  selectedTradelines: ParsedTradeline[];
  onSelectionChange: (selected: ParsedTradeline[]) => void;
  onEditTradeline: (updated: ParsedTradeline) => void;
  onDeleteTradeline: (id: string) => void;
  onAddManualTradeline?: (tradeline: ParsedTradeline) => void;
}

type TradelinesByBureau = Record<string, ParsedTradeline[]>;

export const DisputeWizardStep2SelectTradelines: React.FC<DisputeWizardStep2SelectTradelinesProps> = ({
  tradelines,
  selectedTradelines,
  onSelectionChange,
  onEditTradeline,
  onDeleteTradeline,
  onAddManualTradeline,
}) => {
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editCache, setEditCache] = useState<Record<string, ParsedTradeline>>({});

  const groupByBureau = (tradelines: ParsedTradeline[]): TradelinesByBureau => {
    return tradelines.reduce((acc, tradeline) => {
      const bureau = tradeline.accountCondition ?? "Unknown";
      if (!acc[bureau]) acc[bureau] = [];
      acc[bureau].push(tradeline);
      return acc;
    }, {} as TradelinesByBureau);
  };

  const tradelinesByBureau = groupByBureau(tradelines);

  const toggleSelection = (tradeline: ParsedTradeline) => {
    if (!tradeline.isNegative) return;
    const isSelected = selectedTradelines.some((t) => t.id === tradeline.id);
    if (isSelected) {
      onSelectionChange(selectedTradelines.filter((t) => t.id !== tradeline.id));
    } else {
      onSelectionChange([...selectedTradelines, tradeline]);
    }
  };

  const startEditing = (tradeline: ParsedTradeline) => {
    setEditingId(tradeline.id);
    setEditCache((prev) => ({ ...prev, [tradeline.id]: { ...tradeline } }));
  };

  const cancelEditing = () => {
    setEditingId(null);
  };

  const saveEditing = () => {
    if (editingId && editCache[editingId]) {
      // Debug: log the updated tradeline before saving
      console.log("[DEBUG] Saving edited tradeline:", editCache[editingId]);
      onEditTradeline(editCache[editingId]);
      setEditingId(null);
    }
  };

  const handleEditChange = (id: string, field: keyof ParsedTradeline, value: string | number | undefined) => {
    setEditCache((prev) => {
      const updated = {
        ...prev,
        [id]: {
          ...prev[id],
          [field]: value,
        },
      };
      // Debug: log the edit cache after change
      console.log("[DEBUG] Edit cache after change:", updated);
      return updated;
    });
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between mb-4">
        <Label className="text-lg font-semibold">Step 2: Select Tradelines to Dispute</Label>
        {onAddManualTradeline && (
          <Button
            size="sm"
            variant="outline"
            onClick={() => onAddManualTradeline({} as ParsedTradeline)}
          >
            + Add Tradeline Manually
          </Button>
        )}
      </div>

      {Object.keys(tradelinesByBureau).length === 0 && (
        <p className="text-muted-foreground">No tradelines found.</p>
      )}

      {Object.entries(tradelinesByBureau).map(([bureau, tradelines]) => (
        <div key={bureau}>
          <h3 className="text-xl font-bold mb-3">{bureau}</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
            {tradelines.map((tradeline) => {
              const isSelected = selectedTradelines.some((t) => t.id === tradeline.id);
              const isEditing = editingId === tradeline.id;
              const editLine = editCache[tradeline.id] || tradeline;

              return (
                <Card
                  key={tradeline.id ?? `${tradeline.accountNumber}-${tradeline.creditorName}`}
                  className={`border ${tradeline.isNegative ? "border-red-500 bg-[rgba(255,0,0,0.1)]" : "border-gray-300"}`}
                >
                  <CardHeader>
                    <CardTitle>{tradeline.creditorName || "Unknown Creditor"}</CardTitle>
                    {tradeline.isNegative && <Badge variant="destructive">Negative</Badge>}
                  </CardHeader>
                  <CardContent>
                    {isEditing ? (
                      <>
                        <div className="mb-2">
                          <Label>Account Number</Label>
                          <Input
                            value={editLine.accountNumber || ""}
                            onChange={(e) => handleEditChange(tradeline.id!, "accountNumber", e.target.value)}
                          />
                        </div>
                        <div className="mb-2">
                          <Label>Status</Label>
                          <Input
                            value={editLine.status || ""}
                            onChange={(e) => handleEditChange(tradeline.id!, "status", e.target.value)}
                          />
                        </div>
                        <div className="mb-2">
                          <Label>Balance</Label>
                          <Input
                            type="number"
                            value={editLine.balance ?? ""}
                            onChange={(e) => handleEditChange(tradeline.id!, "balance", parseFloat(e.target.value))}
                          />
                        </div>
                        <div className="mb-2">
                          <Label>Reason for Dispute</Label>
                          <Input
                            value={editLine.negativeReason || ""}
                            onChange={(e) => handleEditChange(tradeline.id!, "negativeReason", e.target.value)}
                          />
                        </div>
                      </>
                    ) : (
                      <>
                        <p>Account #: {tradeline.accountNumber || "N/A"}</p>
                        <p>Status: {tradeline.status || "N/A"}</p>
                        <p>
                          Balance: $
                          {(() => {
                            if (typeof tradeline.balance === "number" && !isNaN(tradeline.balance)) {
                              return tradeline.balance.toFixed(2);
                            }
                            if (typeof tradeline.balance === "string" && !isNaN(Number(tradeline.balance))) {
                              return Number(tradeline.balance).toFixed(2);
                            }
                            if (tradeline.balance === undefined || tradeline.balance === null || tradeline.balance === "") {
                              return "-";
                            }
                            return "0.00";
                          })()}
                        </p>
                        {tradeline.negativeReason && <p>Reason: {tradeline.negativeReason}</p>}
                      </>
                    )}
                  </CardContent>
                  <div className="flex items-center justify-between p-4 pt-0">
                    <div>
                      <input
                        type="checkbox"
                        checked={isSelected}
                        disabled={!tradeline.isNegative}
                        onChange={() => toggleSelection(tradeline)}
                        aria-label={`Select tradeline ${tradeline.creditorName}`}
                      />
                    </div>
                    <div className="space-x-2">
                      {isEditing ? (
                        <>
                          <Button size="sm" variant="outline" onClick={cancelEditing}>
                            Cancel
                          </Button>
                          <Button size="sm" onClick={saveEditing}>
                            Save
                          </Button>
                        </>
                      ) : (
                        <>
                          <Button size="sm" variant="outline" onClick={() => startEditing(tradeline)}>
                            Edit
                          </Button>
                          <Button
                            size="sm"
                            variant="destructive"
                            onClick={() => onDeleteTradeline(tradeline.id!)}
                          >
                            Delete
                          </Button>
                        </>
                      )}
                    </div>
                  </div>
                </Card>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
};
