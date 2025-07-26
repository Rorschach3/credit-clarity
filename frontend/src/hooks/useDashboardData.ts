import { useState, useEffect } from 'react';
import { supabase } from '@/integrations/supabase/client';
import { useAuth } from './use-auth';

export interface DisputeRecord {
  id: string;
  creditor: string;
  account: string;
  status: 'pending' | 'in_progress' | 'completed' | 'rejected';
  priority: 'high' | 'medium' | 'low';
  dateCreated: string;
  dateUpdated: string;
  bureau: string;
  estimatedImpact: number;
  tradelineId?: string;
}

export interface CreditMetrics {
  totalNegativeItems: number;
  itemsDisputed: number;
  itemsResolved: number;
  averageAge: number;
  potentialScoreIncrease: number;
}

export interface DashboardData {
  disputes: DisputeRecord[];
  metrics: CreditMetrics;
  loading: boolean;
  error: string | null;
}

export const useDashboardData = () => {
  const { user } = useAuth();
  const [data, setData] = useState<DashboardData>({
    disputes: [],
    metrics: {
      totalNegativeItems: 0,
      itemsDisputed: 0,
      itemsResolved: 0,
      averageAge: 0,
      potentialScoreIncrease: 0
    },
    loading: true,
    error: null
  });

  const fetchDashboardData = async () => {
    if (!user?.id) {
      setData(prev => ({ ...prev, loading: false }));
      return;
    }

    try {
      setData(prev => ({ ...prev, loading: true, error: null }));

      // Fetch disputes (this represents dispute records)
      const { data: disputes, error: disputeError } = await supabase
        .from('disputes')
        .select('*')
        .eq('user_id', user.id)
        .order('created_at', { ascending: false });

      if (disputeError) {
        console.error('Error fetching disputes:', disputeError);
        // Continue with empty data instead of throwing
      }

      // Fetch tradelines to calculate metrics
      const { data: tradelines, error: tradelinesError } = await supabase
        .from('tradelines')
        .select('*')
        .eq('user_id', user.id);

      if (tradelinesError) {
        console.error('Error fetching tradelines:', tradelinesError);
        // Continue with empty data instead of throwing
      }

      // Transform disputes into dispute records
      const disputeRecords: DisputeRecord[] = (disputes || []).map(dispute => ({
        id: dispute.id,
        creditor: 'Credit Bureau', // Generic name since disputes are sent to bureaus
        account: dispute.id.slice(-8), // Use last 8 chars of ID as account display
        status: dispute.status === 'generated' ? 'pending' : (dispute.status || 'pending') as any,
        priority: 'medium' as const, // Default priority
        dateCreated: dispute.created_at.toString(),
        dateUpdated: dispute.modified_at?.toString() || dispute.created_at.toString(),
        bureau: 'Multiple', // Disputes can target multiple bureaus
        estimatedImpact: 25 // Default estimated impact
      }));

      // Calculate metrics from tradelines
      const negativeItems = (tradelines || []).filter(t => 
        t.account_status && (
          t.account_status.toLowerCase().includes('charged off') ||
          t.account_status.toLowerCase().includes('collection') ||
          t.account_status.toLowerCase().includes('late') ||
          t.account_status.toLowerCase().includes('delinquent')
        )
      );

      const metrics: CreditMetrics = {
        totalNegativeItems: negativeItems.length,
        itemsDisputed: disputeRecords.length,
        itemsResolved: disputeRecords.filter(d => d.status === 'completed').length,
        averageAge: calculateAverageAge(negativeItems),
        potentialScoreIncrease: disputeRecords.reduce((sum, d) => sum + d.estimatedImpact, 0)
      };

      setData({
        disputes: disputeRecords,
        metrics,
        loading: false,
        error: null
      });

    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      setData(prev => ({
        ...prev,
        loading: false,
        error: error instanceof Error ? error.message : 'Failed to fetch dashboard data'
      }));
    }
  };

  // Calculate average age of negative items in months
  const calculateAverageAge = (items: any[]): number => {
    if (items.length === 0) return 0;
    
    const now = new Date();
    const totalMonths = items.reduce((sum, item) => {
      if (item.date_opened) {
        const openDate = new Date(item.date_opened);
        const monthsDiff = (now.getFullYear() - openDate.getFullYear()) * 12 + 
                          (now.getMonth() - openDate.getMonth());
        return sum + monthsDiff;
      }
      return sum + 18; // Default to 18 months if no date
    }, 0);

    return Math.round(totalMonths / items.length);
  };

  // Refresh data
  const refreshData = () => {
    fetchDashboardData();
  };

  useEffect(() => {
    fetchDashboardData();
  }, [user?.id]);

  return {
    ...data,
    refreshData
  };
};