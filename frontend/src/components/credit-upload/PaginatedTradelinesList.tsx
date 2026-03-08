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
import { Loader2 } from 'lucide-react';
import { usePaginatedTradelines } from '@/hooks/usePaginatedTradelines';

interface PaginatedTradelinesListProps {
  userId: string;
  onSelect?: (id: string) => void;
  onUpdate?: (id: string, updates: any) => void;
  onDelete?: (id: string) => void;
  selectedIds?: Set<string>;
}

const BUREAUS = ['equifax', 'experian', 'transunion'] as const;
const BUREAU_LABELS: Record<string, string> = {
  equifax: 'Equifax',
  experian: 'Experian',
  transunion: 'TransUnion',
};
const BUREAU_COLORS: Record<string, string> = {
  equifax: 'bg-red-600 text-white border-red-600',
  experian: 'bg-blue-700 text-white border-blue-700',
  transunion: 'bg-green-700 text-white border-green-700',
};

const PaginatedTradelinesList: React.FC<PaginatedTradelinesListProps> = ({
  userId,
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
    goToNextPage,
    goToPreviousPage,
  } = usePaginatedTradelines({
    userId,
    initialOptions: { pageSize: 10 },
    autoLoad: true
  });

  const [activeBureau, setActiveBureau] = React.useState<string | null>(null);

  const visibleTradelines = activeBureau
    ? tradelines.filter(t => t.credit_bureau?.toLowerCase() === activeBureau)
    : tradelines;

  const bureauCounts = React.useMemo(() => {
    return BUREAUS.reduce<Record<string, number>>((acc, b) => {
      acc[b] = tradelines.filter(t => t.credit_bureau?.toLowerCase() === b).length;
      return acc;
    }, {} as Record<string, number>);
  }, [tradelines]);

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
      <CardHeader className="flex flex-col gap-3">
        <div className="flex flex-row items-center justify-between">
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
        </div>

        {/* Bureau filter tabs */}
        <div className="flex items-center gap-2 flex-wrap">
          <button
            onClick={() => setActiveBureau(null)}
            className={`px-3 py-1 rounded-full text-xs font-medium border transition-colors ${
              activeBureau === null
                ? 'bg-foreground text-background border-foreground'
                : 'border-border hover:bg-muted'
            }`}
          >
            All ({pagination.totalCount})
          </button>
          {BUREAUS.map(b => (
            <button
              key={b}
              onClick={() => setActiveBureau(activeBureau === b ? null : b)}
              className={`px-3 py-1 rounded-full text-xs font-medium border transition-colors ${
                activeBureau === b
                  ? BUREAU_COLORS[b]
                  : 'border-border hover:bg-muted'
              }`}
            >
              {BUREAU_LABELS[b]} ({bureauCounts[b]})
            </button>
          ))}
        </div>
      </CardHeader>

      <CardContent>
        {loading && tradelines.length === 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {[0, 1, 2].map(i => (
              <div key={i} className="space-y-3">
                <Skeleton className="h-9 w-full rounded-lg" />
                {Array.from({ length: 3 }).map((_, j) => (
                  <Skeleton key={j} className="h-24 w-full" />
                ))}
              </div>
            ))}
          </div>
        ) : (
          <>
            {/* 3-column bureau layout */}
            {(() => {
              const grouped = BUREAUS.reduce<Record<string, typeof tradelines>>((acc, b) => {
                acc[b] = visibleTradelines.filter(t => (t.credit_bureau || '').toLowerCase() === b);
                return acc;
              }, {} as Record<string, typeof tradelines>);

              const unassigned = visibleTradelines.filter(
                t => !BUREAUS.some(b => b === (t.credit_bureau || '').toLowerCase())
              );

              const BUREAU_COL_STYLES: Record<string, { header: string; border: string }> = {
                equifax:    { header: 'bg-red-600',   border: 'border-red-200 dark:border-red-800' },
                experian:   { header: 'bg-blue-700',  border: 'border-blue-200 dark:border-blue-800' },
                transunion: { header: 'bg-green-700', border: 'border-green-200 dark:border-green-800' },
              };

              return (
                <div className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {BUREAUS.map(bureau => (
                      <div key={bureau} className={`rounded-lg border ${BUREAU_COL_STYLES[bureau].border} overflow-hidden`}>
                        <div className={`${BUREAU_COL_STYLES[bureau].header} px-4 py-2 flex items-center justify-between`}>
                          <span className="font-semibold text-white text-sm">{BUREAU_LABELS[bureau]}</span>
                          <Badge variant="secondary" className="text-xs bg-white/20 text-white border-0">
                            {grouped[bureau].length}
                          </Badge>
                        </div>
                        <div className="p-3 space-y-2 min-h-[80px]">
                          {grouped[bureau].length === 0 ? (
                            <p className="text-muted-foreground text-xs text-center py-4">
                              No tradelines for this bureau
                            </p>
                          ) : (
                            grouped[bureau].map(tradeline => (
                              <div
                                key={tradeline.id}
                                className={`p-3 border rounded-lg text-sm transition-colors ${
                                  selectedIds.has(tradeline.id) ? 'bg-blue-50 border-blue-200' : 'bg-card hover:bg-muted/50'
                                }`}
                              >
                                <div className="flex items-start justify-between gap-2">
                                  <div className="min-w-0">
                                    <p className="font-medium truncate">{tradeline.creditor_name}</p>
                                    <p className="text-xs text-muted-foreground font-mono">{tradeline.account_number}</p>
                                    <p className="text-xs text-muted-foreground">{tradeline.account_type}</p>
                                  </div>
                                  <button
                                    onClick={() => onDelete?.(tradeline.id)}
                                    className="text-red-500 hover:text-red-700 text-lg leading-none flex-shrink-0"
                                  >
                                    ×
                                  </button>
                                </div>
                                <div className="mt-2 flex items-center justify-between">
                                  <span className="font-medium">{tradeline.account_balance}</span>
                                  <Badge variant={tradeline.is_negative ? 'destructive' : 'secondary'} className="text-xs">
                                    {tradeline.account_status}
                                  </Badge>
                                </div>
                              </div>
                            ))
                          )}
                        </div>
                      </div>
                    ))}
                  </div>

                  {unassigned.length > 0 && (
                    <div className="rounded-lg border border-dashed border-muted-foreground/30 overflow-hidden">
                      <div className="bg-muted px-4 py-2 flex items-center justify-between">
                        <span className="font-semibold text-sm text-muted-foreground">Unassigned Bureau</span>
                        <Badge variant="outline" className="text-xs">{unassigned.length}</Badge>
                      </div>
                      <div className="p-3 grid grid-cols-1 md:grid-cols-3 gap-2">
                        {unassigned.map(tradeline => (
                          <div key={tradeline.id} className="p-3 border rounded-lg text-sm bg-card hover:bg-muted/50">
                            <div className="flex items-start justify-between gap-2">
                              <div className="min-w-0">
                                <p className="font-medium truncate">{tradeline.creditor_name}</p>
                                <p className="text-xs text-muted-foreground font-mono">{tradeline.account_number}</p>
                              </div>
                              <button
                                onClick={() => onDelete?.(tradeline.id)}
                                className="text-red-500 hover:text-red-700 text-lg leading-none flex-shrink-0"
                              >
                                ×
                              </button>
                            </div>
                            <div className="mt-2 flex items-center justify-between">
                              <span className="font-medium">{tradeline.account_balance}</span>
                              <Badge variant={tradeline.is_negative ? 'destructive' : 'secondary'} className="text-xs">
                                {tradeline.account_status}
                              </Badge>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {visibleTradelines.length === 0 && (
                    <div className="text-center py-8 text-muted-foreground">
                      {activeBureau ? `No tradelines for ${BUREAU_LABELS[activeBureau]} on this page.` : 'No tradelines found.'}
                    </div>
                  )}
                </div>
              );
            })()}

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