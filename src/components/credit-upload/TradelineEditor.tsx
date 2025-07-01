
import React from 'react';
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ParsedTradeline } from "@/utils/tradelineParser";

interface TradelineEditorProps {
  tradeline: ParsedTradeline;
  index: number;
  isSelected: boolean;
  onUpdate: (index: number, updated: Partial<ParsedTradeline>) => void;
  onDelete: (index: number) => void;
  onSelect: (id: string, selected: boolean) => void;
}

function safeValue<T extends string | number | null | undefined>(v: T): string {
  if (typeof v === "number") return String(v);
  return v ?? "";
}

export const TradelineEditor: React.FC<TradelineEditorProps> = ({
  tradeline,
  index,
  isSelected,
  onUpdate,
  onDelete,
  onSelect
}) => {
  return (
    <div className="border p-4 rounded mb-3 space-y-2">
      <div className="flex items-center mb-2">
        <Checkbox
          id={`select-tradeline-${tradeline.id}`}
          checked={isSelected}
          onCheckedChange={(checked) => onSelect(tradeline.id || '', checked as boolean)}
          className="mr-2"
        />
        <Label htmlFor={`select-tradeline-${tradeline.id}`} className="font-semibold">
          Select for Dispute
        </Label>
      </div>
      
      <div>
        <label className="block font-semibold mb-1">Creditor Name</label>
        <Input
          value={safeValue(tradeline.creditor_name)}
          onChange={(e) => onUpdate(index, { creditor_name: e.target.value })}
        />
      </div>
      
      <div>
        <label className="block font-semibold mb-1">Account Number</label>
        <Input
          value={safeValue(tradeline.account_number)}
          onChange={(e) => onUpdate(index, { account_number: e.target.value })}
        />
      </div>
      
      <div>
        <label className="block font-semibold mb-1">Status</label>
        <Select
          value={safeValue(tradeline.account_status)}
          onValueChange={(value) => onUpdate(index, {
            account_status: value as "" | "open" | "closed" | "in_collection" | "charged_off" | "disputed"
          })}
        >
          <SelectTrigger className="w-full">
            <SelectValue placeholder="Select status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="open">Open</SelectItem>
            <SelectItem value="closed">Closed</SelectItem>
            <SelectItem value="in_collection">In Collection</SelectItem>
            <SelectItem value="charged_off">Charged Off</SelectItem>
            <SelectItem value="disputed">Disputed</SelectItem>
          </SelectContent>
        </Select>
      </div>
      
      <div>
        <label className="block font-semibold mb-1">Balance</label>
        <Input
          type="text"
          value={safeValue(tradeline.account_balance)}
          onChange={(e) => onUpdate(index, { account_balance: e.target.value })}
        />
      </div>
      
      <div>
        <label className="block font-semibold mb-1">Credit Limit</label>
        <Input
          type="text"
          value={safeValue(tradeline.credit_limit)}
          onChange={(e) => onUpdate(index, { credit_limit: e.target.value })}
        />
      </div>
      
      <div>
        <label className="block font-semibold mb-1">Date Opened</label>
        <Input
          type="date"
          value={safeValue(tradeline.date_opened)}
          onChange={(e) => onUpdate(index, { date_opened: e.target.value })}
        />
      </div>
      
      <div>
        <label className="block font-semibold mb-1">Credit Bureau</label>
        <Select
          value={safeValue(tradeline.credit_bureau)}
          onValueChange={(value) => onUpdate(index, {
            credit_bureau: value as "equifax" | "transunion" | "experian"
          })}
        >
          <SelectTrigger className="w-full">
            <SelectValue placeholder="Select credit bureau" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="equifax">Equifax</SelectItem>
            <SelectItem value="experian">Experian</SelectItem>
            <SelectItem value="transunion">TransUnion</SelectItem>
          </SelectContent>
        </Select>
      </div>
      
      <div>
        <label className="block font-semibold mb-1">Monthly Payment</label>
        <Input
          type="text"
          value={safeValue(tradeline.monthly_payment)}
          onChange={(e) => onUpdate(index, { monthly_payment: e.target.value })}
        />
      </div>
      
      <div>
        <Button
          variant="destructive"
          size="sm"
          onClick={() => onDelete(index)}
          className="mt-2"
        >
          Delete
        </Button>
      </div>
    </div>
  );
};
