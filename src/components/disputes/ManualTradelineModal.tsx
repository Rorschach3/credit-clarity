
import React, { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { ParsedTradeline } from '@/types';
import { v4 as uuidv4 } from 'uuid';
import { useAuth } from '@/hooks/use-auth';

interface Props {
  onClose: () => void;
  onAdd: (tradeline: ParsedTradeline) => void;
}

const initialTradeline: Partial<ParsedTradeline> = {
  creditor_name: '',
  account_number: '',
  account_balance: '$0',
  account_status: '',
  account_type: 'credit_card',
  credit_limit: '$0',
  date_opened: '',
  monthly_payment: '$0',
  is_negative: false,
  dispute_count: 0,
  credit_bureau: '',
  raw_text: ''
};

export function ManualTradelineModal({ onClose, onAdd }: Props) {
  const [tradeline, setTradeline] = useState<Partial<ParsedTradeline>>(initialTradeline);
  const { user } = useAuth();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!tradeline.creditor_name || !tradeline.account_number) {
      return;
    }

    const newTradeline: ParsedTradeline = {
      id: uuidv4(),
      creditor_name: tradeline.creditor_name,
      account_number: tradeline.account_number,
      account_balance: tradeline.account_balance || '$0',
      account_status: tradeline.account_status as "" | "open" | "closed" | "in_collection" | "charged_off" | "disputed" || "",
      account_type: tradeline.account_type as "" | "credit_card" | "mortgage" | "auto_loan" | "personal_loan" | "collection" || "credit_card",
      credit_limit: tradeline.credit_limit || '$0',
      date_opened: tradeline.date_opened || '',
      monthly_payment: tradeline.monthly_payment || '$0',
      is_negative: Boolean(tradeline.is_negative),
      dispute_count: Number(tradeline.dispute_count) || 0,
      credit_bureau: tradeline.credit_bureau as "equifax" | "transunion" | "experian" || "",
      created_at: new Date().toISOString(),
      raw_text: tradeline.raw_text || '',
      user_id: user?.id || ''
    };

    onAdd(newTradeline);
    onClose();
  };

  const updateTradeline = (field: keyof ParsedTradeline, value: any) => {
    setTradeline(prev => ({ ...prev, [field]: value }));
  };

  return (
    <Dialog open onOpenChange={onClose}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Add Tradeline Manually</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <Label htmlFor="creditor_name">Creditor Name</Label>
            <Input
              id="creditor_name"
              value={tradeline.creditor_name || ''}
              onChange={(e) => updateTradeline('creditor_name', e.target.value)}
              required
            />
          </div>

          <div>
            <Label htmlFor="account_number">Account Number</Label>
            <Input
              id="account_number"
              value={tradeline.account_number || ''}
              onChange={(e) => updateTradeline('account_number', e.target.value)}
              required
            />
          </div>

          <div>
            <Label htmlFor="account_balance">Account Balance</Label>
            <Input
              id="account_balance"
              value={tradeline.account_balance || ''}
              onChange={(e) => updateTradeline('account_balance', e.target.value)}
            />
          </div>

          <div>
            <Label htmlFor="account_status">Account Status</Label>
            <Select
              value={tradeline.account_status || ''}
              onValueChange={(value) => updateTradeline('account_status', value)}
            >
              <SelectTrigger>
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
            <Label htmlFor="credit_bureau">Credit Bureau</Label>
            <Select
              value={tradeline.credit_bureau || ''}
              onValueChange={(value) => updateTradeline('credit_bureau', value)}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select bureau" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="equifax">Equifax</SelectItem>
                <SelectItem value="experian">Experian</SelectItem>
                <SelectItem value="transunion">TransUnion</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="flex gap-2 pt-4">
            <Button type="button" variant="outline" onClick={onClose} className="flex-1">
              Cancel
            </Button>
            <Button type="submit" className="flex-1">
              Add Tradeline
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
