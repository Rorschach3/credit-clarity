import { useQuery } from '@tanstack/react-query';
import { useAuth } from '@/hooks/use-auth';
import { dashboardApi } from '@/services/api';
import { queryKeys } from '@/lib/react-query';

// Optimized dashboard hook that batches all data fetching
export const useDashboardData = () => {
  const { user } = useAuth();
  
  return useQuery({
    queryKey: queryKeys.dashboard(user?.id || ''),
    queryFn: () => dashboardApi.getDashboardData(user!.id),
    enabled: !!user?.id,
    staleTime: 2 * 60 * 1000, // 2 minutes for dashboard data
    gcTime: 5 * 60 * 1000, // 5 minutes in cache
    // Disable automatic refetching to prevent too many calls
    refetchOnWindowFocus: false,
    refetchOnReconnect: true,
  });
};

// Hook specifically for dashboard metrics with computed values
export const useDashboardMetrics = () => {
  const { data, isLoading, error } = useDashboardData();
  
  // Enhanced metrics computation
  const enhancedMetrics = data ? {
    ...data.metrics,
    // Computed percentages
    negativePercentage: data.metrics.totalTradelines > 0 
      ? Math.round((data.metrics.negativeTradelines / data.metrics.totalTradelines) * 100)
      : 0,
    disputeSuccessRate: data.metrics.totalDisputes > 0
      ? Math.round((data.metrics.resolvedDisputes / data.metrics.totalDisputes) * 100)
      : 0,
    // Bureau distribution
    bureauDistribution: {
      Experian: data.tradelines.filter(t => t.credit_bureau === 'Experian').length,
      Equifax: data.tradelines.filter(t => t.credit_bureau === 'Equifax').length,
      TransUnion: data.tradelines.filter(t => t.credit_bureau === 'TransUnion').length,
    },
    // Recent activity (last 30 days)
    recentActivity: {
      newDisputes: data.disputes.filter(d => {
        const disputeDate = new Date(d.created_at);
        const thirtyDaysAgo = new Date();
        thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
        return disputeDate >= thirtyDaysAgo;
      }).length,
      resolvedThisMonth: data.disputes.filter(d => {
        if (d.status !== 'completed' || !d.modified_at) return false;
        const resolvedDate = new Date(d.modified_at);
        const thirtyDaysAgo = new Date();
        thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
        return resolvedDate >= thirtyDaysAgo;
      }).length,
    },
    // Potential score impact estimation
    potentialScoreIncrease: data.metrics.negativeTradelines * 15, // Rough estimate
  } : null;

  return {
    metrics: enhancedMetrics,
    rawData: data,
    isLoading,
    error,
    // Convenience flags
    hasData: !!data,
    hasProfile: !!data?.profile,
    hasTradelines: (data?.tradelines.length || 0) > 0,
    hasDisputes: (data?.disputes.length || 0) > 0,
  };
};

// Specialized hook for chart data to prevent recalculation
export const useDashboardChartData = () => {
  const { data, isLoading } = useDashboardData();
  
  const chartData = data ? {
    // Status distribution for pie chart
    statusDistribution: [
      { 
        name: 'Positive', 
        value: data.metrics.positiveTradelines, 
        color: '#22c55e',
        percentage: data.metrics.totalTradelines > 0 
          ? Math.round((data.metrics.positiveTradelines / data.metrics.totalTradelines) * 100)
          : 0
      },
      { 
        name: 'Negative', 
        value: data.metrics.negativeTradelines, 
        color: '#ef4444',
        percentage: data.metrics.totalTradelines > 0 
          ? Math.round((data.metrics.negativeTradelines / data.metrics.totalTradelines) * 100)
          : 0
      },
    ],
    
    // Bureau distribution for bar chart
    bureauDistribution: [
      { bureau: 'Experian', count: data.tradelines.filter(t => t.credit_bureau === 'Experian').length },
      { bureau: 'Equifax', count: data.tradelines.filter(t => t.credit_bureau === 'Equifax').length },
      { bureau: 'TransUnion', count: data.tradelines.filter(t => t.credit_bureau === 'TransUnion').length },
    ],
    
    // Timeline data for line chart (last 6 months)
    timelineData: Array.from({ length: 6 }, (_, i) => {
      const date = new Date();
      date.setMonth(date.getMonth() - i);
      const monthYear = date.toISOString().slice(0, 7); // YYYY-MM format
      
      const disputesThisMonth = data.disputes.filter(d => 
        d.created_at.startsWith(monthYear)
      ).length;
      
      const resolvedThisMonth = data.disputes.filter(d => 
        d.status === 'completed' && 
        d.modified_at && 
        d.modified_at.startsWith(monthYear)
      ).length;
      
      return {
        month: date.toLocaleDateString('en-US', { month: 'short', year: 'numeric' }),
        disputes: disputesThisMonth,
        resolved: resolvedThisMonth,
      };
    }).reverse(),
    
    // Progress over time
    progressData: data.disputes.map(dispute => ({
      date: new Date(dispute.created_at).toLocaleDateString(),
      status: dispute.status,
      createdAt: dispute.created_at,
    })).sort((a, b) => new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime()),
    
  } : null;

  return {
    chartData,
    isLoading,
    hasChartData: !!chartData,
  };
};