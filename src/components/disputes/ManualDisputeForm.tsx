
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import { useToast } from "@/hooks/use-toast";
import { type NegativeItem } from "@/types/negative-item";

type AccountType = "credit_card" | "loan" | "mortgage" | "auto_loan" | "student_loan" | "collection";

interface ManualDisputeFormProps {
  onItemCreated: (item: NegativeItem) => void;
}

export function ManualDisputeForm({ onItemCreated }: ManualDisputeFormProps) {
  const [formData, setFormData] = useState({
    creditorName: "",
    accountNumber: "",
    accountType: "credit_card" as AccountType,
    amount: "",
    dateReported: "",
    reason: "",
    bureaus: [] as string[]
  });
  const { toast } = useToast();

  const handleBureauChange = (bureau: string, checked: boolean) => {
    setFormData(prev => ({
      ...prev,
      bureaus: checked 
        ? [...prev.bureaus, bureau]
        : prev.bureaus.filter(b => b !== bureau)
    }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.creditorName || !formData.accountNumber || formData.bureaus.length === 0) {
      toast({
        title: "Missing Information",
        description: "Please fill in all required fields and select at least one bureau.",
        variant: "destructive"
      });
      return;
    }

    const newItem: NegativeItem = {
      id: `manual-${Date.now()}`,
      creditorName: formData.creditorName,
      accountNumber: formData.accountNumber,
      accountType: formData.accountType,
      balance: parseFloat(formData.amount.replace(/[$,]/g, '')) || 0,
      isNegative: true,
      amount: formData.amount,
      dateReported: formData.dateReported,
      bureaus: formData.bureaus,
      reason: formData.reason || "Account disputed",
      status: "disputed"
    };

    onItemCreated(newItem);
    
    // Reset form
    setFormData({
      creditorName: "",
      accountNumber: "",
      accountType: "credit_card",
      amount: "",
      dateReported: "",
      reason: "",
      bureaus: []
    });

    toast({
      title: "Item Added",
      description: "Manual dispute item has been added successfully.",
    });
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>Add Manual Dispute Item</CardTitle>
        <CardDescription>
          Manually add a negative item to dispute if not found in your credit report scan
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Label htmlFor="creditorName">Creditor Name *</Label>
              <Input
                id="creditorName"
                value={formData.creditorName}
                onChange={(e) => setFormData(prev => ({ ...prev, creditorName: e.target.value }))}
                placeholder="e.g., Capital One"
                required
              />
            </div>
            <div>
              <Label htmlFor="accountNumber">Account Number *</Label>
              <Input
                id="accountNumber"
                value={formData.accountNumber}
                onChange={(e) => setFormData(prev => ({ ...prev, accountNumber: e.target.value }))}
                placeholder="e.g., ****1234"
                required
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Label htmlFor="accountType">Account Type</Label>
              <Select value={formData.accountType} onValueChange={(value: AccountType) => 
                setFormData(prev => ({ ...prev, accountType: value }))
              }>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="credit_card">Credit Card</SelectItem>
                  <SelectItem value="loan">Personal Loan</SelectItem>
                  <SelectItem value="mortgage">Mortgage</SelectItem>
                  <SelectItem value="auto_loan">Auto Loan</SelectItem>
                  <SelectItem value="student_loan">Student Loan</SelectItem>
                  <SelectItem value="collection">Collection Account</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label htmlFor="amount">Amount</Label>
              <Input
                id="amount"
                value={formData.amount}
                onChange={(e) => setFormData(prev => ({ ...prev, amount: e.target.value }))}
                placeholder="e.g., $1,500"
              />
            </div>
          </div>

          <div>
            <Label htmlFor="dateReported">Date Reported</Label>
            <Input
              id="dateReported"
              type="date"
              value={formData.dateReported}
              onChange={(e) => setFormData(prev => ({ ...prev, dateReported: e.target.value }))}
            />
          </div>

          <div>
            <Label htmlFor="reason">Dispute Reason</Label>
            <Textarea
              id="reason"
              value={formData.reason}
              onChange={(e) => setFormData(prev => ({ ...prev, reason: e.target.value }))}
              placeholder="e.g., This account does not belong to me"
              rows={3}
            />
          </div>

          <div>
            <Label>Credit Bureaus Reporting *</Label>
            <div className="flex flex-wrap gap-4 mt-2">
              {['Experian', 'Equifax', 'TransUnion'].map((bureau) => (
                <div key={bureau} className="flex items-center space-x-2">
                  <Checkbox
                    id={bureau}
                    checked={formData.bureaus.includes(bureau)}
                    onCheckedChange={(checked) => handleBureauChange(bureau, checked as boolean)}
                  />
                  <Label htmlFor={bureau}>{bureau}</Label>
                </div>
              ))}
            </div>
          </div>

          <Button type="submit" className="w-full">
            Add Dispute Item
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
