import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
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
import { Loader2 } from 'lucide-react';
import { usePaginatedTradelines } from '@/hooks/usePaginatedTradelines';
import { PaginationOptions, ParsedTradeline } from '@/utils/tradelineParser';
import { EditableTradelineCard } from './EditableTradelineCard';

interface PaginatedTradelinesListProps {
  userId: string;
  onUpdate?: (id: string, updates: Partial<ParsedTradeline>) => void;
  onDelete?: (id: string) => void;
}

const PaginatedTradelinesList: React.FC<PaginatedTradelinesListProps> = ({
  userId,
  onUpdate,
  onDelete
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
            {/* Sorting Controls */}
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium">Sort by:</span>
                <Select 
                  value={`${currentSort.field}-${currentSort.direction}`}
                  onValueChange={(value) => {
                    const [field, direction] = value.split('-') as [PaginationOptions['sortBy'], PaginationOptions['sortOrder']];
                    setCurrentSort({ field, direction });
                    setSorting(field, direction);
                  }}
                >
                  <SelectTrigger className="w-48">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="creditor_name-asc">Creditor A-Z</SelectItem>
                    <SelectItem value="creditor_name-desc">Creditor Z-A</SelectItem>
                    <SelectItem value="account_balance-asc">Balance Low-High</SelectItem>
                    <SelectItem value="account_balance-desc">Balance High-Low</SelectItem>
                    <SelectItem value="created_at-asc">Date Added Oldest</SelectItem>
                    <SelectItem value="created_at-desc">Date Added Newest</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Editable Tradeline Cards */}
            <div className="space-y-4">
              {tradelines.map((tradeline) => (
                <EditableTradelineCard
                  key={tradeline.id}
                  tradeline={tradeline}
                  onUpdate={(updates) => {
                    if (onUpdate) {
                      onUpdate(tradeline.id, updates);
                    }
                  }}
                  onDelete={() => {
                    if (onDelete) {
                      onDelete(tradeline.id);
                    }
                  }}
                />
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