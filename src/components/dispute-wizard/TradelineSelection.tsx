import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
import { Button } from '@/components/ui/button';
import { FileText, CheckSquare, Square } from 'lucide-react';
import { type ParsedTradeline } from '@/utils/tradelineParser';

interface TradelineSelectionProps {
  negativeTradelines: ParsedTradeline[];
  selectedTradelines: string[];
  onToggleSelection: (tradelineId: string) => void;
  onSelectAll: () => void;
  onDeselectAll: () => void;
}

export const TradelineSelection: React.FC<TradelineSelectionProps> = ({
  negativeTradelines,
  selectedTradelines,
  onToggleSelection,
  onSelectAll,
  onDeselectAll
}) => {
  if (negativeTradelines.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Negative Tradelines
            <Badge variant="secondary" className="ml-auto">0 found</Badge>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <p className="text-muted-foreground">No negative tradelines found in your credit report.</p>
            <p className="text-sm text-muted-foreground mt-2">
              Upload your credit report from the tradelines page to get started.
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  const allSelected = selectedTradelines.length === negativeTradelines.length;
  const someSelected = selectedTradelines.length > 0;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg flex items-center gap-2">
          <FileText className="h-5 w-5" />
          Negative Tradelines ({negativeTradelines.length})
          <Badge variant="secondary" className="ml-auto">
            {selectedTradelines.length} selected
          </Badge>
        </CardTitle>
        <div className="flex gap-2 mt-2">
          <Button
            variant="outline"
            size="sm"
            onClick={allSelected ? onDeselectAll : onSelectAll}
            className="flex items-center gap-2"
          >
            {allSelected ? <Square className="h-4 w-4" /> : <CheckSquare className="h-4 w-4" />}
            {allSelected ? 'Deselect All' : 'Select All'}
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-3 max-h-96 overflow-y-auto">
          {negativeTradelines.map((tradeline) => (
            <div
              key={tradeline.id}
              className={`p-3 border rounded-lg transition-colors ${
                selectedTradelines.includes(tradeline.id)
                  ? 'border-blue-300 bg-blue-50 dark:bg-blue-900/20'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <div className="flex items-start gap-3">
                <Checkbox
                  checked={selectedTradelines.includes(tradeline.id)}
                  onCheckedChange={() => onToggleSelection(tradeline.id)}
                  className="mt-0.5"
                />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <h4 className="font-medium text-sm">
                      {tradeline.creditor_name || 'Unknown Creditor'}
                    </h4>
                    <Badge variant="destructive" className="ml-2">
                      {tradeline.credit_bureau}
                    </Badge>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-2 mt-2 text-xs text-muted-foreground">
                    <div>
                      <span className="font-medium">Account:</span> {tradeline.account_number || 'N/A'}
                    </div>
                    <div>
                      <span className="font-medium">Status:</span> {tradeline.account_status || 'N/A'}
                    </div>
                    <div>
                      <span className="font-medium">Balance:</span> {tradeline.account_balance || 'N/A'}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
};