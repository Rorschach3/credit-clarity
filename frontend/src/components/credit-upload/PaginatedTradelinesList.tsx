import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { 
  Pagination,
  PaginationContent,
  PaginationEllipsis,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from '@/components/ui/pagination';
import { Skeleton } from '@/components/ui/skeleton';
import { ArrowUpDown, ChevronUp, ChevronDown, Loader2 } from 'lucide-react';
import { usePaginatedTradelines } from '@/hooks/usePaginatedTradelines';
import { PaginationOptions } from '@/utils/tradelineParser';

interface PaginatedTradelinesListProps {
  userId: string;
  onSelect?: (id: string) => void;
  onUpdate?: (id: string, updates: any) => void;
  onDelete?: (id: string) => void;
  selectedIds?: Set<string>;
}

const PaginatedTradelinesList: React.FC<PaginatedTradelinesListProps> = ({
  userId,
  onSelect,
  onUpdate,
  onDelete,
  selectedIds = new Set()
}) => {
  const {
    tradelines,
    pagination,
    loading,
    error,
    loadPage,
    refresh,
    setPageSize,
    setSorting,
    goToNextPage,
    goToPreviousPage,
    goToFirstPage,
    goToLastPage,
  } = usePaginatedTradelines({
    userId,
    initialOptions: { pageSize: 10 },
    autoLoad: true
  });

  const [currentSort, setCurrentSort] = React.useState<{
    field: PaginationOptions['sortBy'];
    direction: PaginationOptions['sortOrder'];
  }>({
    field: 'created_at',
    direction: 'desc'
  });

  const handleSort = (field: PaginationOptions['sortBy']) => {
    const newDirection = 
      currentSort.field === field && currentSort.direction === 'desc' 
        ? 'asc' 
        : 'desc';
    
    setCurrentSort({ field, direction: newDirection });
    setSorting(field, newDirection);
  };

  const generatePageNumbers = () => {
    const pages = [];
    const { page, totalPages } = pagination;
    
    // Always show first page
    if (totalPages > 0) {
      pages.push(1);
    }
    
    // Add ellipsis if there's a gap
    if (page > 3) {
      pages.push('ellipsis-start');
    }
    
    // Add pages around current page
    for (let i = Math.max(2, page - 1); i <= Math.min(totalPages - 1, page + 1); i++) {
      if (!pages.includes(i)) {
        pages.push(i);
      }
    }
    
    // Add ellipsis if there's a gap
    if (page < totalPages - 2) {
      pages.push('ellipsis-end');
    }
    
    // Always show last page
    if (totalPages > 1) {
      pages.push(totalPages);
    }
    
    return pages;
  };

  const SortIcon = ({ field }: { field: PaginationOptions['sortBy'] }) => {
    if (currentSort.field !== field) {
      return <ArrowUpDown className="h-4 w-4" />;
    }
    return currentSort.direction === 'asc' 
      ? <ChevronUp className="h-4 w-4" />
      : <ChevronDown className="h-4 w-4" />;
  };

  if (error) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="text-center">
            <p className="text-red-600 mb-4">Error loading tradelines: {error}</p>
            <Button onClick={refresh} variant="outline">
              Try Again
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>
          Tradelines 
          {!loading && (
            <span className="text-sm text-muted-foreground ml-2">
              ({pagination.totalCount} total)
            </span>
          )}
        </CardTitle>
        <div className="flex items-center gap-2">
          <span className="text-sm text-muted-foreground">Rows per page:</span>
          <Select 
            value={pagination.pageSize.toString()} 
            onValueChange={(value) => setPageSize(Number(value))}
          >
            <SelectTrigger className="w-20">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="5">5</SelectItem>
              <SelectItem value="10">10</SelectItem>
              <SelectItem value="20">20</SelectItem>
              <SelectItem value="50">50</SelectItem>
            </SelectContent>
          </Select>
          <Button onClick={refresh} variant="outline" size="sm" disabled={loading}>
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Refresh'}
          </Button>
        </div>
      </CardHeader>

      <CardContent>
        {loading && tradelines.length === 0 ? (
          <div className="space-y-3">
            {Array.from({ length: 5 }).map((_, i) => (
              <Skeleton key={i} className="h-16 w-full" />
            ))}
          </div>
        ) : (
          <>
            {/* Table Header */}
            <div className="grid grid-cols-12 gap-4 p-3 bg-muted rounded-lg mb-4 text-sm font-medium">
              <div className="col-span-1">
                <input
                  type="checkbox"
                  className="rounded"
                  // Add select all functionality here if needed
                />
              </div>
              <div className="col-span-3">
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-auto p-0 font-medium"
                  onClick={() => handleSort('creditor_name')}
                >
                  Creditor
                  <SortIcon field="creditor_name" />
                </Button>
              </div>
              <div className="col-span-2">Account Number</div>
              <div className="col-span-2">
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-auto p-0 font-medium"
                  onClick={() => handleSort('account_balance')}
                >
                  Balance
                  <SortIcon field="account_balance" />
                </Button>
              </div>
              <div className="col-span-2">Status</div>
              <div className="col-span-1">
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-auto p-0 font-medium"
                  onClick={() => handleSort('created_at')}
                >
                  Date
                  <SortIcon field="created_at" />
                </Button>
              </div>
              <div className="col-span-1">Actions</div>
            </div>

            {/* Table Body */}
            <div className="space-y-2">
              {tradelines.map((tradeline) => (
                <div
                  key={tradeline.id}
                  className={`grid grid-cols-12 gap-4 p-3 border rounded-lg transition-colors ${
                    selectedIds.has(tradeline.id) ? 'bg-blue-50 border-blue-200' : 'hover:bg-muted/50'
                  }`}
                >
                  <div className="col-span-1 flex items-center">
                    <input
                      type="checkbox"
                      className="rounded"
                      checked={selectedIds.has(tradeline.id)}
                      onChange={() => onSelect?.(tradeline.id)}
                    />
                  </div>
                  <div className="col-span-3 flex items-center">
                    <div>
                      <p className="font-medium">{tradeline.creditor_name}</p>
                      <p className="text-sm text-muted-foreground">{tradeline.account_type}</p>
                    </div>
                  </div>
                  <div className="col-span-2 flex items-center">
                    <span className="font-mono text-sm">
                      {tradeline.account_number}
                    </span>
                  </div>
                  <div className="col-span-2 flex items-center">
                    <span className="font-medium">{tradeline.account_balance}</span>
                  </div>
                  <div className="col-span-2 flex items-center">
                    <Badge variant={tradeline.is_negative ? "destructive" : "secondary"}>
                      {tradeline.account_status}
                    </Badge>
                  </div>
                  <div className="col-span-1 flex items-center">
                    <span className="text-sm text-muted-foreground">
                      {new Date(tradeline.created_at).toLocaleDateString()}
                    </span>
                  </div>
                  <div className="col-span-1 flex items-center">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => onDelete?.(tradeline.id)}
                      className="h-8 w-8 p-0 text-red-600 hover:text-red-700"
                    >
                      ×
                    </Button>
                  </div>
                </div>
              ))}
            </div>

            {tradelines.length === 0 && !loading && (
              <div className="text-center py-8 text-muted-foreground">
                No tradelines found.
              </div>
            )}

            {/* Pagination */}
            {pagination.totalPages > 1 && (
              <div className="mt-6 flex items-center justify-between">
                <p className="text-sm text-muted-foreground">
                  Showing {((pagination.page - 1) * pagination.pageSize) + 1} to{' '}
                  {Math.min(pagination.page * pagination.pageSize, pagination.totalCount)} of{' '}
                  {pagination.totalCount} results
                </p>

                <Pagination>
                  <PaginationContent>
                    <PaginationItem>
                      <PaginationPrevious 
                        onClick={goToPreviousPage}
                        className={!pagination.hasPrevious ? 'pointer-events-none opacity-50' : 'cursor-pointer'}
                      />
                    </PaginationItem>

                    {generatePageNumbers().map((pageNum, index) => (
                      <PaginationItem key={index}>
                        {pageNum === 'ellipsis-start' || pageNum === 'ellipsis-end' ? (
                          <PaginationEllipsis />
                        ) : (
                          <PaginationLink
                            onClick={() => loadPage(pageNum as number)}
                            isActive={pageNum === pagination.page}
                            className="cursor-pointer"
                          >
                            {pageNum}
                          </PaginationLink>
                        )}
                      </PaginationItem>
                    ))}

                    <PaginationItem>
                      <PaginationNext 
                        onClick={goToNextPage}
                        className={!pagination.hasNext ? 'pointer-events-none opacity-50' : 'cursor-pointer'}
                      />
                    </PaginationItem>
                  </PaginationContent>
                </Pagination>
              </div>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
};

export default PaginatedTradelinesList;