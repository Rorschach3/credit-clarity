import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Search, Filter, Download, Plus, Trash2 } from 'lucide-react';
import { useAuth } from '@/hooks/use-auth';
import { usePaginatedTradelines } from '@/hooks/usePaginatedTradelines';
import PaginatedTradelinesList from '@/components/credit-upload/PaginatedTradelinesList';
import { toast } from 'sonner';

const TradelinesManagementPage = () => {
  const { user } = useAuth();
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');

  const {
    tradelines,
    pagination,
    loading,
    error,
    refresh,
  } = usePaginatedTradelines({
    userId: user?.id || '',
    initialOptions: { pageSize: 20 },
    autoLoad: true
  });

  const handleSelect = (id: string) => {
    setSelectedIds(prev => {
      const newSet = new Set(prev);
      if (newSet.has(id)) {
        newSet.delete(id);
      } else {
        newSet.add(id);
      }
      return newSet;
    });
  };

  const handleSelectAll = () => {
    if (selectedIds.size === tradelines.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(tradelines.map(t => t.id)));
    }
  };

  const handleBulkDelete = async () => {
    if (selectedIds.size === 0) return;
    
    const confirmed = window.confirm(`Delete ${selectedIds.size} selected tradeline(s)?`);
    if (!confirmed) return;

    try {
      // Implement bulk delete logic here
      toast.success(`Deleted ${selectedIds.size} tradeline(s)`);
      setSelectedIds(new Set());
      refresh();
    } catch (error) {
      toast.error('Failed to delete tradelines');
    }
  };

  const handleExport = () => {
    // Implement export logic here
    toast.success('Export started...');
  };

  const filteredStats = {
    total: pagination.totalCount,
    negative: tradelines.filter(t => t.is_negative).length,
    positive: tradelines.filter(t => !t.is_negative).length,
  };

  if (!user) {
    return (
      <div className="min-h-screen bg-background text-foreground py-10 px-4">
        <Card className="max-w-2xl mx-auto">
          <CardContent className="p-6">
            <p className="text-center text-muted-foreground">
              Please log in to manage your tradelines.
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background text-foreground py-10 px-4 md:px-10">
      <div className="max-w-7xl mx-auto space-y-6">
        
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold">Tradelines Management</h1>
            <p className="text-muted-foreground">
              Manage and review all your credit tradelines
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button onClick={handleExport} variant="outline" size="sm">
              <Download className="h-4 w-4 mr-2" />
              Export
            </Button>
            <Button size="sm">
              <Plus className="h-4 w-4 mr-2" />
              Add Tradeline
            </Button>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Total Tradelines</p>
                  <p className="text-2xl font-bold">{filteredStats.total}</p>
                </div>
                <Badge variant="secondary">{filteredStats.total}</Badge>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Negative Items</p>
                  <p className="text-2xl font-bold text-red-600">{filteredStats.negative}</p>
                </div>
                <Badge variant="destructive">{filteredStats.negative}</Badge>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Positive Items</p>
                  <p className="text-2xl font-bold text-green-600">{filteredStats.positive}</p>
                </div>
                <Badge variant="secondary">{filteredStats.positive}</Badge>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Filters and Search */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Filters</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col sm:flex-row gap-4">
              <div className="flex-1">
                <Label htmlFor="search">Search Tradelines</Label>
                <div className="relative mt-1">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    id="search"
                    placeholder="Search by creditor name, account number..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-10"
                  />
                </div>
              </div>
              
              <div className="w-full sm:w-48">
                <Label htmlFor="status-filter">Status Filter</Label>
                <Select value={statusFilter} onValueChange={setStatusFilter}>
                  <SelectTrigger className="mt-1">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Status</SelectItem>
                    <SelectItem value="positive">Positive Only</SelectItem>
                    <SelectItem value="negative">Negative Only</SelectItem>
                    <SelectItem value="open">Open Accounts</SelectItem>
                    <SelectItem value="closed">Closed Accounts</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Bulk Actions */}
        {selectedIds.size > 0 && (
          <Card className="bg-blue-50 border-blue-200">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">
                  {selectedIds.size} tradeline(s) selected
                </span>
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setSelectedIds(new Set())}
                  >
                    Clear Selection
                  </Button>
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={handleBulkDelete}
                  >
                    <Trash2 className="h-4 w-4 mr-2" />
                    Delete Selected
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Paginated Table */}
        <PaginatedTradelinesList
          userId={user.id}
          onSelect={handleSelect}
          selectedIds={selectedIds}
        />
      </div>
    </div>
  );
};

export default TradelinesManagementPage;