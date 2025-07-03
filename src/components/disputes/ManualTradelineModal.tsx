
import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { ParsedTradeline } from "@/utils/tradelineParser";

interface ManualTradelineModalProps {
  onClose: () => void;
  onAdd: (tradeline: ParsedTradeline) => void;
}

export const ManualTradelineModal: React.FC<ManualTradelineModalProps> = ({ onClose, onAdd }) => {
  const [formData, setFormData] = useState<Partial<ParsedTradeline>>({
    creditor_name: "",
    account_number: "",
    account_balance: "",
    credit_limit: "",
    monthly_payment: "",
    date_opened: "",
    account_type: "",
    account_status: "",
    credit_bureau: "",
    is_negative: false,
    dispute_count: 0,
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    const newTradeline: ParsedTradeline = {
      id: crypto.randomUUID(),
      user_id: "",
      creditor_name: formData.creditor_name || "",
      account_number: formData.account_number || "",
      account_balance: formData.account_balance || "",
      created_at: new Date().toISOString(),
      credit_limit: formData.credit_limit || "",
      monthly_payment: formData.monthly_payment || "",
      date_opened: formData.date_opened || "",
      is_negative: formData.is_negative || false,
      account_type: formData.account_type || "",
      account_status: formData.account_status || "",
      credit_bureau: formData.credit_bureau || "",
      dispute_count: formData.dispute_count || 0,
    };

    onAdd(newTradeline);
    onClose();
  };

  return (
    <Dialog open={true} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Add Manual Tradeline</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="creditor_name">Creditor Name</Label>
              <Input
                id="creditor_name"
                value={formData.creditor_name}
                onChange={(e) => setFormData(prev => ({ ...prev, creditor_name: e.target.value }))}
                required
              />
            </div>
            <div>
              <Label htmlFor="account_number">Account Number</Label>
              <Input
                id="account_number"
                value={formData.account_number}
                onChange={(e) => setFormData(prev => ({ ...prev, account_number: e.target.value }))}
                required
              />
            </div>
            <div>
              <Label htmlFor="account_balance">Account Balance</Label>
              <Input
                id="account_balance"
                value={formData.account_balance}
                onChange={(e) => setFormData(prev => ({ ...prev, account_balance: e.target.value }))}
              />
            </div>
            <div>
              <Label htmlFor="credit_limit">Credit Limit</Label>
              <Input
                id="credit_limit"
                value={formData.credit_limit}
                onChange={(e) => setFormData(prev => ({ ...prev, credit_limit: e.target.value }))}
              />
            </div>
            <div>
              <Label htmlFor="monthly_payment">Monthly Payment</Label>
              <Input
                id="monthly_payment"
                value={formData.monthly_payment}
                onChange={(e) => setFormData(prev => ({ ...prev, monthly_payment: e.target.value }))}
              />
            </div>
            <div>
              <Label htmlFor="date_opened">Date Opened</Label>
              <Input
                id="date_opened"
                type="date"
                value={formData.date_opened}
                onChange={(e) => setFormData(prev => ({ ...prev, date_opened: e.target.value }))}
              />
            </div>
            <div>
              <Label htmlFor="account_type">Account Type</Label>
              <Select onValueChange={(value) => setFormData(prev => ({ ...prev, account_type: value }))}>
                <SelectTrigger>
                  <SelectValue placeholder="Select account type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="credit_card">Credit Card</SelectItem>
                  <SelectItem value="loan">Loan</SelectItem>
                  <SelectItem value="mortgage">Mortgage</SelectItem>
                  <SelectItem value="auto_loan">Auto Loan</SelectItem>
                  <SelectItem value="student_loan">Student Loan</SelectItem>
                  <SelectItem value="collection">Collection</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label htmlFor="account_status">Account Status</Label>
              <Select onValueChange={(value) => setFormData(prev => ({ ...prev, account_status: value }))}>
                <SelectTrigger>
                  <SelectValue placeholder="Select account status" />
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
              <Select onValueChange={(value) => setFormData(prev => ({ ...prev, credit_bureau: value }))}>
                <SelectTrigger>
                  <SelectValue placeholder="Select credit bureau" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="equifax">Equifax</SelectItem>
                  <SelectItem value="transunion">TransUnion</SelectItem>
                  <SelectItem value="experian">Experian</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <input
              type="checkbox"
              id="is_negative"
              checked={formData.is_negative}
              onChange={(e) => setFormData(prev => ({ ...prev, is_negative: e.target.checked }))}
            />
            <Label htmlFor="is_negative">Is Negative Item</Label>
          </div>
          <div className="flex justify-end space-x-2">
            <Button type="button" variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit">Add Tradeline</Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
};
