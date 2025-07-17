import { useState, useMemo, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useAuth } from "@/hooks/use-auth";
import { Database } from "@/integrations/supabase/types";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { useNavigate } from "react-router-dom";
import { CreditNavbar } from "@/components/navbar/CreditNavbar";
import { AlertCircle, CheckCircle, X, RefreshCw } from "lucide-react";
import { useTradelines, useUpdateTradeline, useDeleteTradeline } from "@/hooks/queries/useTradelinesQueries";

// Define Tradeline type from Supabase schema
type Tradeline = Database["public"]["Tables"]["tradelines"]["Row"];

// Credit Bureau constants
const CREDIT_BUREAUS = ['Experian', 'Equifax', 'TransUnion'] as const;
type CreditBureau = typeof CREDIT_BUREAUS[number];

// Enhanced tradeline type for UI
interface EnhancedTradeline extends Tradeline {
  _isUnverified?: boolean;
  _originalBureau?: CreditBureau;
}

// Selection state interface
interface SelectionState {
  selectedBureau: CreditBureau | null;
  selectedTradelineIds: Set<string>;
}

const NegativeTradelinesPage = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  
  // Use React Query for data fetching
  const { data: accounts = [], isLoading, error: queryError, refetch } = useTradelines();
  const updateTradelineMutation = useUpdateTradeline();
  const deleteTradelineMutation = useDeleteTradeline();
  
  const [editingAccount, setEditingAccount] = useState<Tradeline | null>(null);
  const [selection, setSelection] = useState<SelectionState>({
    selectedBureau: null,
    selectedTradelineIds: new Set()
  });
  
  // Convert query error to string for compatibility
  const error = queryError instanceof Error ? queryError.message : null;

  // Simplified grouping logic - avoid duplicating unverified tradelines
  const tradelinesByBureau = useMemo(() => {
    const grouped: Record<CreditBureau, EnhancedTradeline[]> = {
      'Experian': [],
      'Equifax': [],
      'TransUnion': []
    };

    accounts.forEach(account => {
      const bureau = account.credit_bureau as CreditBureau;
      
      if (bureau && CREDIT_BUREAUS.includes(bureau)) {
        // Add to specific bureau
        grouped[bureau].push({
          ...account,
          _originalBureau: bureau
        });
      } else {
        // For accounts without bureau info, add a note but don't duplicate
        // Instead, show them in a separate "Unknown Bureau" section or handle differently
        console.warn(`Account ${account.id} has no bureau specified`);
      }
    });

    return grouped;
  }, [accounts]);

  // Get summary statistics for each bureau
  const bureauStats = useMemo(() => {
    const stats: Record<CreditBureau, { total: number; negative: number; positive: number }> = {
      'Experian': { total: 0, negative: 0, positive: 0 },
      'Equifax': { total: 0, negative: 0, positive: 0 },
      'TransUnion': { total: 0, negative: 0, positive: 0 }
    };

    Object.entries(tradelinesByBureau).forEach(([bureau, tradelines]) => {
      const bureauKey = bureau as CreditBureau;
      stats[bureauKey].total = tradelines.length;
      stats[bureauKey].negative = tradelines.filter(t => t.is_negative).length;
      stats[bureauKey].positive = tradelines.filter(t => !t.is_negative).length;
    });

    return stats;
  }, [tradelinesByBureau]);

  // Find accounts that appear on some bureaus but not others
  const bureauDiscrepancies = useMemo(() => {
    const accountMap = new Map<string, { account: Tradeline; bureaus: CreditBureau[] }>();

    accounts.forEach(account => {
      const key = `${account.creditor_name}-${account.account_number}`;
      const bureau = account.credit_bureau as CreditBureau;
      
      if (!accountMap.has(key)) {
        accountMap.set(key, { account, bureaus: [] });
      }
      
      if (bureau && CREDIT_BUREAUS.includes(bureau)) {
        accountMap.get(key)!.bureaus.push(bureau);
      }
    });

    return Array.from(accountMap.values())
      .filter(({ bureaus }) => bureaus.length > 0 && bureaus.length < 3)
      .map(({ account, bureaus }) => ({
        creditor: account.creditor_name || '',
        account: account.account_number || '',
        presentOn: bureaus,
        missingFrom: CREDIT_BUREAUS.filter(b => !bureaus.includes(b))
      }));
  }, [accounts]);

  // Simplified selection handlers
  const handleBureauChange = useCallback((bureau: CreditBureau | null) => {
    setSelection({
      selectedBureau: bureau,
      selectedTradelineIds: new Set()
    });
  }, []);

  const handleTradelineToggle = useCallback((tradelineId: string, bureau: CreditBureau) => {
    setSelection(prev => {
      // If no bureau selected or different bureau, switch to this bureau
      if (!prev.selectedBureau || prev.selectedBureau !== bureau) {
        return {
          selectedBureau: bureau,
          selectedTradelineIds: new Set([tradelineId])
        };
      }

      // Toggle selection for same bureau
      const newIds = new Set(prev.selectedTradelineIds);
      if (newIds.has(tradelineId)) {
        newIds.delete(tradelineId);
      } else {
        newIds.add(tradelineId);
      }

      return {
        selectedBureau: newIds.size > 0 ? bureau : null,
        selectedTradelineIds: newIds
      };
    });
  }, []);

  const handleSelectAllNegative = useCallback((bureau: CreditBureau) => {
    const negativeIds = tradelinesByBureau[bureau]
      .filter(t => t.is_negative)
      .map(t => t.id);
    
    setSelection({
      selectedBureau: bureau,
      selectedTradelineIds: new Set(negativeIds)
    });
  }, [tradelinesByBureau]);

  const handleClearSelection = useCallback(() => {
    setSelection({
      selectedBureau: null,
      selectedTradelineIds: new Set()
    });
  }, []);

  // Save edit using React Query mutation
  const handleSaveEdit = useCallback(async (updatedTradeline: Tradeline) => {
    updateTradelineMutation.mutate(
      { id: updatedTradeline.id, updates: updatedTradeline },
      {
        onSuccess: () => {
          setEditingAccount(null);
        },
        onError: (error) => {
          console.error("Error updating tradeline:", error);
        }
      }
    );
  }, [updateTradelineMutation]);

  // Delete tradeline using React Query mutation
  const handleDeleteTradeline = useCallback(async (tradelineId: string) => {
    if (!window.confirm("Are you sure you want to delete this tradeline?")) return;

    deleteTradelineMutation.mutate(tradelineId, {
      onSuccess: () => {
        // Remove from selection if selected
        setSelection(prev => {
          const newIds = new Set(prev.selectedTradelineIds);
          newIds.delete(tradelineId);
          return {
            selectedBureau: newIds.size > 0 ? prev.selectedBureau : null,
            selectedTradelineIds: newIds
          };
        });
      },
      onError: (error) => {
        console.error("Error deleting tradeline:", error);
      }
    });
  }, [deleteTradelineMutation]);

  const handleGenerateDisputePacket = useCallback(() => {
    if (!selection.selectedBureau || selection.selectedTradelineIds.size === 0) return;

    const selectedTradelines = accounts.filter(acc => 
      selection.selectedTradelineIds.has(acc.id)
    );

    navigate("/dispute-wizard", {
      state: {
        initialSelectedTradelines: selectedTradelines,
        selectedBureau: selection.selectedBureau
      }
    });
  }, [selection, accounts, navigate]);

  // Render tradeline card component
  const renderTradelineCard = useCallback((tradeline: EnhancedTradeline, bureau: CreditBureau) => {
    const isSelectable = !selection.selectedBureau || selection.selectedBureau === bureau;
    const isSelected = selection.selectedTradelineIds.has(tradeline.id);
    
    return (
      <Card 
        key={`${tradeline.id}-${bureau}`}
        className={`
          transition-all duration-200 hover:shadow-md
          ${tradeline.is_negative 
            ? 'border-red-500 bg-red-50 dark:bg-red-900/20' 
            : 'border-green-500 bg-green-50 dark:bg-green-900/20'
          }
          ${!isSelectable ? 'opacity-50 cursor-not-allowed' : ''}
          ${isSelected ? 'ring-2 ring-blue-500' : ''}
        `}
      >
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm font-medium">
              {tradeline.creditor_name || 'Unknown Creditor'}
            </CardTitle>
            <Badge variant={tradeline.is_negative ? "destructive" : "default"}>
              {tradeline.is_negative ? "Negative" : "Positive"}
            </Badge>
          </div>
        </CardHeader>
        
        <CardContent className="space-y-3">
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={isSelected}
              disabled={!isSelectable}
              onChange={() => handleTradelineToggle(tradeline.id, bureau)}
              className="rounded"
            />
            <span className={`text-sm ${!isSelectable ? 'text-muted-foreground' : ''}`}>
              {isSelectable ? 'Select for dispute' : 'Select a bureau first'}
            </span>
          </div>
          
          <div className="text-sm space-y-1">
            <p><strong>Account:</strong> {tradeline.account_number || 'N/A'}</p>
            <p><strong>Status:</strong> {tradeline.account_status || 'N/A'}</p>
            <p><strong>Balance:</strong> {tradeline.account_balance || 'N/A'}</p>
            <p><strong>Date Opened:</strong> {tradeline.date_opened || 'N/A'}</p>
            <p><strong>Type:</strong> {tradeline.account_type || 'N/A'}</p>
          </div>
          
          <div className="flex gap-2 pt-2">
            <Button
              size="sm"
              variant="outline"
              onClick={() => setEditingAccount(tradeline)}
              className="flex-1"
            >
              Edit
            </Button>
            <Button
              size="sm"
              variant="destructive"
              onClick={() => handleDeleteTradeline(tradeline.id)}
              className="flex-1"
            >
              Delete
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }, [selection, handleTradelineToggle, handleDeleteTradeline]);

  // Loading state
  if (isLoading) {
    return (
      <div className="min-h-screen bg-background text-foreground">
        <CreditNavbar />
        <div className="container mx-auto px-4 py-8">
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
              <p className="text-muted-foreground">Loading tradelines...</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Empty state
  if (accounts.length === 0) {
    return (
      <div className="min-h-screen bg-background text-foreground">
        <CreditNavbar />
        <div className="container mx-auto px-4 py-8">
          <div className="text-center py-12">
            <p className="text-muted-foreground mb-4">No tradelines found.</p>
            <Button onClick={() => navigate('/credit-report-upload')}>
              Upload Credit Report
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background text-foreground">
      <CreditNavbar />
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">Tradelines by Credit Bureau</h1>
          <p className="text-muted-foreground mb-4">
            Select tradelines from one credit bureau to generate dispute packets
          </p>
          
          {/* Selection Status */}
          {selection.selectedBureau ? (
            <div className="flex items-center gap-2 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
              <CheckCircle className="h-4 w-4 text-blue-600" />
              <Badge variant="default" className="bg-blue-600">
                {selection.selectedBureau} Selected
              </Badge>
              <span className="text-sm text-blue-700 dark:text-blue-300">
                {selection.selectedTradelineIds.size} tradeline(s) selected
              </span>
              <Button 
                variant="outline" 
                size="sm" 
                onClick={handleClearSelection}
                className="ml-auto"
              >
                <X className="h-4 w-4 mr-1" />
                Clear
              </Button>
            </div>
          ) : (
            <div className="flex items-center gap-2 p-3 bg-gray-50 dark:bg-gray-900/20 border border-gray-200 dark:border-gray-800 rounded-lg">
              <span className="text-sm text-muted-foreground">
                Select tradelines from any bureau to start building your dispute packet
              </span>
            </div>
          )}
        </div>

        {/* Error Display */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
            <div className="flex items-center gap-2">
              <AlertCircle className="h-4 w-4 text-red-600" />
              <p className="text-red-700 dark:text-red-300">{error}</p>
            </div>
          </div>
        )}

        {/* Bureau Discrepancies */}
        {bureauDiscrepancies.length > 0 && (
          <Card className="mb-6 border-yellow-200 bg-yellow-50 dark:bg-yellow-900/20">
            <CardHeader>
              <CardTitle className="text-yellow-800 dark:text-yellow-200 flex items-center gap-2">
                <AlertCircle className="h-5 w-5" />
                Potential Bureau Discrepancies ({bureauDiscrepancies.length})
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-yellow-700 dark:text-yellow-300 mb-3">
                These accounts appear on some credit bureaus but not others.
              </p>
              <div className="space-y-2">
                {bureauDiscrepancies.map((discrepancy, index) => (
                  <div key={index} className="flex items-center justify-between p-2 bg-white dark:bg-gray-800 rounded text-sm">
                    <div>
                      <span className="font-medium">{discrepancy.creditor}</span>
                      <span className="text-muted-foreground ml-2">({discrepancy.account})</span>
                    </div>
                    <div className="flex gap-2">
                      <span className="text-green-600">
                        ✓ {discrepancy.presentOn.join(', ')}
                      </span>
                      <span className="text-red-600">
                        ✗ {discrepancy.missingFrom.join(', ')}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Bureau Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          {CREDIT_BUREAUS.map((bureau) => {
            const isSelected = selection.selectedBureau === bureau;
            const isDisabled = selection.selectedBureau && selection.selectedBureau !== bureau;
            const tradelines = tradelinesByBureau[bureau];
            
            return (
              <div key={bureau} className="space-y-4">
                {/* Bureau Header */}
                <Card className={`
                  ${isSelected ? 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800' : 
                    isDisabled ? 'bg-gray-50 dark:bg-gray-900/20 border-gray-200 dark:border-gray-800 opacity-60' : 
                    'bg-primary/5 border-primary/20'}
                `}>
                  <CardHeader className="pb-3">
                    <CardTitle className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span>{bureau}</span>
                        {isSelected && (
                          <Badge variant="default" className="bg-blue-600 text-xs">
                            Selected
                          </Badge>
                        )}
                      </div>
                      <Badge variant="secondary">
                        {bureauStats[bureau].total} total
                      </Badge>
                    </CardTitle>
                    <div className="flex gap-4 text-sm">
                      <span className="text-green-600 dark:text-green-400">
                        {bureauStats[bureau].positive} positive
                      </span>
                      <span className="text-red-600 dark:text-red-400">
                        {bureauStats[bureau].negative} negative
                      </span>
                    </div>
                  </CardHeader>
                </Card>

                {/* Bureau Actions */}
                {bureauStats[bureau].negative > 0 && (
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleSelectAllNegative(bureau)}
                      className="text-xs"
                    >
                      Select All Negative ({bureauStats[bureau].negative})
                    </Button>
                  </div>
                )}

                {/* Tradelines */}
                <div className="space-y-3">
                  {tradelines.length === 0 ? (
                    <Card className="p-6 text-center border-dashed">
                      <p className="text-muted-foreground">No tradelines found for {bureau}</p>
                    </Card>
                  ) : (
                    tradelines.map((tradeline) => renderTradelineCard(tradeline, bureau))
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* Action Bar */}
        <div className="flex flex-wrap gap-4 items-center justify-between bg-muted/50 p-4 rounded-lg">
          <div className="flex items-center gap-4">
            <span className="text-sm text-muted-foreground">
              {selection.selectedTradelineIds.size} tradeline{selection.selectedTradelineIds.size !== 1 ? 's' : ''} selected
              {selection.selectedBureau && (
                <span className="ml-2 text-blue-600 dark:text-blue-400">
                  for {selection.selectedBureau}
                </span>
              )}
            </span>
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              onClick={handleClearSelection}
              disabled={selection.selectedTradelineIds.size === 0}
            >
              Clear Selection
            </Button>
            <Button
              disabled={selection.selectedTradelineIds.size === 0 || !selection.selectedBureau}
              onClick={handleGenerateDisputePacket}
              className="bg-green-600 hover:bg-green-700"
            >
              Generate {selection.selectedBureau} Dispute Packet ({selection.selectedTradelineIds.size})
            </Button>
          </div>
        </div>

        {/* Edit Dialog */}
        {editingAccount && (
          <EditTradelineDialog
            tradeline={editingAccount}
            onSave={handleSaveEdit}
            onCancel={() => setEditingAccount(null)}
          />
        )}
      </div>
    </div>
  );
};

// Separate component for the edit dialog
const EditTradelineDialog = ({ 
  tradeline, 
  onSave, 
  onCancel 
}: { 
  tradeline: Tradeline; 
  onSave: (updatedTradeline: Tradeline) => void; 
  onCancel: () => void; 
}) => {
  const [formData, setFormData] = useState<Tradeline>(tradeline);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave(formData);
  };

  return (
    <Dialog open={true} onOpenChange={onCancel}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Edit Tradeline</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="grid gap-4 py-4">
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="creditor_name" className="text-right">
              Creditor
            </Label>
            <Input 
              id="creditor_name" 
              name="creditor_name" 
              value={formData.creditor_name || ''} 
              onChange={handleChange} 
              className="col-span-3" 
            />
          </div>
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="account_number" className="text-right">
              Account Number
            </Label>
            <Input 
              id="account_number" 
              name="account_number" 
              value={formData.account_number || ''} 
              onChange={handleChange} 
              className="col-span-3" 
            />
          </div>
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="account_status" className="text-right">
              Status
            </Label>
            <Input 
              id="account_status" 
              name="account_status" 
              value={formData.account_status || ''} 
              onChange={handleChange} 
              className="col-span-3" 
            />
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={onCancel}>
              Cancel
            </Button>
            <Button type="submit">Save changes</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};

export default NegativeTradelinesPage;