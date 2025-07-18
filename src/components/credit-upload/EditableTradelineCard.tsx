import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Trash2, Edit, Save, X } from 'lucide-react';
import { ParsedTradeline } from '@/utils/tradelineParser';
import { toast } from 'sonner';

interface EditableTradelineCardProps {
  tradeline: ParsedTradeline;
  onUpdate: (updates: Partial<ParsedTradeline>) => void;
  onDelete: () => void;
}

export const EditableTradelineCard: React.FC<EditableTradelineCardProps> = ({
  tradeline,
  onUpdate,
  onDelete,
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editedTradeline, setEditedTradeline] = useState<ParsedTradeline>(tradeline);

  const handleSave = () => {
    onUpdate(editedTradeline);
    setIsEditing(false);
    toast.success('Tradeline updated successfully');
  };

  const handleCancel = () => {
    setEditedTradeline(tradeline);
    setIsEditing(false);
  };

  const handleFieldChange = (field: keyof ParsedTradeline, value: string | boolean) => {
    setEditedTradeline(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleDelete = () => {
    if (window.confirm('Are you sure you want to delete this tradeline?')) {
      onDelete();
      toast.success('Tradeline deleted successfully');
    }
  };

  return (
    <Card className="relative">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg flex items-center gap-2">
            {isEditing ? (
              <Input
                value={editedTradeline.creditor_name || ''}
                onChange={(e) => handleFieldChange('creditor_name', e.target.value)}
                className="font-semibold"
                placeholder="Creditor Name"
              />
            ) : (
              tradeline.creditor_name || 'Unknown Creditor'
            )}
            {tradeline.is_negative && (
              <Badge variant="destructive">Negative</Badge>
            )}
          </CardTitle>
          <div className="flex items-center gap-2">
            {isEditing ? (
              <>
                <Button size="sm" onClick={handleSave} className="h-8 w-8 p-0">
                  <Save className="h-4 w-4" />
                </Button>
                <Button size="sm" variant="outline" onClick={handleCancel} className="h-8 w-8 p-0">
                  <X className="h-4 w-4" />
                </Button>
              </>
            ) : (
              <>
                <Button size="sm" variant="outline" onClick={() => setIsEditing(true)} className="h-8 w-8 p-0">
                  <Edit className="h-4 w-4" />
                </Button>
                <Button size="sm" variant="destructive" onClick={handleDelete} className="h-8 w-8 p-0">
                  <Trash2 className="h-4 w-4" />
                </Button>
              </>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent className="pt-0">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div>
            <Label className="text-sm font-medium">Account Number</Label>
            {isEditing ? (
              <Input
                value={editedTradeline.account_number || ''}
                onChange={(e) => handleFieldChange('account_number', e.target.value)}
                placeholder="Account Number"
              />
            ) : (
              <p className="text-sm text-muted-foreground">{tradeline.account_number || 'N/A'}</p>
            )}
          </div>

          <div>
            <Label className="text-sm font-medium">Account Type</Label>
            {isEditing ? (
              <Select
                value={editedTradeline.account_type || ''}
                onValueChange={(value) => handleFieldChange('account_type', value)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select Type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="credit_card">Credit Card</SelectItem>
                  <SelectItem value="mortgage">Mortgage</SelectItem>
                  <SelectItem value="auto_loan">Auto Loan</SelectItem>
                  <SelectItem value="student_loan">Student Loan</SelectItem>
                  <SelectItem value="loan">Personal Loan</SelectItem>
                  <SelectItem value="collection">Collection</SelectItem>
                </SelectContent>
              </Select>
            ) : (
              <p className="text-sm text-muted-foreground">{tradeline.account_type || 'N/A'}</p>
            )}
          </div>

          <div>
            <Label className="text-sm font-medium">Account Status</Label>
            {isEditing ? (
              <Select
                value={editedTradeline.account_status || ''}
                onValueChange={(value) => handleFieldChange('account_status', value)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="open">Open</SelectItem>
                  <SelectItem value="closed">Closed</SelectItem>
                  <SelectItem value="current-account">Current</SelectItem>
                  <SelectItem value="late">Late</SelectItem>
                  <SelectItem value="collections">Collections</SelectItem>
                  <SelectItem value="charged_off">Charged Off</SelectItem>
                </SelectContent>
              </Select>
            ) : (
              <p className="text-sm text-muted-foreground">{tradeline.account_status || 'N/A'}</p>
            )}
          </div>

          <div>
            <Label className="text-sm font-medium">Balance</Label>
            {isEditing ? (
              <Input
                value={editedTradeline.account_balance || ''}
                onChange={(e) => handleFieldChange('account_balance', e.target.value)}
                placeholder="$0.00"
              />
            ) : (
              <p className="text-sm text-muted-foreground">{tradeline.account_balance || 'N/A'}</p>
            )}
          </div>

          <div>
            <Label className="text-sm font-medium">Credit Limit</Label>
            {isEditing ? (
              <Input
                value={editedTradeline.credit_limit || ''}
                onChange={(e) => handleFieldChange('credit_limit', e.target.value)}
                placeholder="$0.00"
              />
            ) : (
              <p className="text-sm text-muted-foreground">{tradeline.credit_limit || 'N/A'}</p>
            )}
          </div>

          <div>
            <Label className="text-sm font-medium">Monthly Payment</Label>
            {isEditing ? (
              <Input
                value={editedTradeline.monthly_payment || ''}
                onChange={(e) => handleFieldChange('monthly_payment', e.target.value)}
                placeholder="$0.00"
              />
            ) : (
              <p className="text-sm text-muted-foreground">{tradeline.monthly_payment || 'N/A'}</p>
            )}
          </div>

          <div>
            <Label className="text-sm font-medium">Credit Bureau</Label>
            {isEditing ? (
              <Select
                value={editedTradeline.credit_bureau || ''}
                onValueChange={(value) => handleFieldChange('credit_bureau', value)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select Bureau" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="Experian">Experian</SelectItem>
                  <SelectItem value="Equifax">Equifax</SelectItem>
                  <SelectItem value="TransUnion">TransUnion</SelectItem>
                </SelectContent>
              </Select>
            ) : (
              <p className="text-sm text-muted-foreground">{tradeline.credit_bureau || 'N/A'}</p>
            )}
          </div>

          <div>
            <Label className="text-sm font-medium">Date Opened</Label>
            {isEditing ? (
              <Input
                type="date"
                value={editedTradeline.date_opened || ''}
                onChange={(e) => handleFieldChange('date_opened', e.target.value)}
              />
            ) : (
              <p className="text-sm text-muted-foreground">
                {tradeline.date_opened ? new Date(tradeline.date_opened).toLocaleDateString() : 'N/A'}
              </p>
            )}
          </div>

          <div className="flex items-center gap-2">
            <Label className="text-sm font-medium">Negative Account</Label>
            {isEditing ? (
              <input
                type="checkbox"
                checked={editedTradeline.is_negative || false}
                onChange={(e) => handleFieldChange('is_negative', e.target.checked)}
                className="h-4 w-4"
              />
            ) : (
              <div className={`h-4 w-4 rounded border-2 ${tradeline.is_negative ? 'bg-red-500 border-red-500' : 'border-gray-300'}`} />
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};