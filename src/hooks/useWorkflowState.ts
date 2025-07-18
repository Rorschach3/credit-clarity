import { useState, useEffect } from 'react';
import { useAuth } from './use-auth';
import { usePersistentTradelines } from './usePersistentTradelines';
import { usePersistentProfile } from './usePersistentProfile';

interface WorkflowState {
  hasUploadedReports: boolean;
  hasSelectedTradelines: boolean;
  hasGeneratedLetter: boolean;
  hasUploadedDocuments: boolean;
  hasGeneratedPacket: boolean;
  tradelinesCount: number;
  negativeTradelinesCount: number;
  selectedTradelinesCount: number;
  isProfileComplete: boolean;
}

export const useWorkflowState = () => {
  const { user } = useAuth();
  const { tradelines, getNegativeTradelines } = usePersistentTradelines();
  const { isProfileComplete } = usePersistentProfile();
  
  const [workflowState, setWorkflowState] = useState<WorkflowState>({
    hasUploadedReports: false,
    hasSelectedTradelines: false,
    hasGeneratedLetter: false,
    hasUploadedDocuments: false,
    hasGeneratedPacket: false,
    tradelinesCount: 0,
    negativeTradelinesCount: 0,
    selectedTradelinesCount: 0,
    isProfileComplete: false
  });

  // Check if user has generated dispute letters before
  const checkForExistingDisputePackets = async () => {
    if (!user?.id) return { hasLetters: false, hasPackets: false };
    
    try {
      const { supabase } = await import('@/integrations/supabase/client');
      
      // First check if table exists by doing a simple count query
      const { data, error } = await supabase
        .from('dispute_packets')
        .select('id, packet_status', { count: 'exact', head: false })
        .eq('user_id', user.id)
        .limit(10);
      
      if (error) {
        console.log('Dispute packets table not available yet:', error.message);
        return { hasLetters: false, hasPackets: false };
      }
      
      const hasLetters = data && data.length > 0;
      const hasPackets = data && data.some(packet => packet.packet_status === 'ready');
      
      return { hasLetters, hasPackets };
    } catch (error) {
      console.error('Error checking dispute packets:', error);
      return { hasLetters: false, hasPackets: false };
    }
  };

  // Check if user has uploaded documents
  const checkForUploadedDocuments = async () => {
    if (!user?.id) return false;
    
    try {
      const { supabase } = await import('@/integrations/supabase/client');
      
      // Check session first
      const { data: session } = await supabase.auth.getSession();
      if (!session?.session) {
        console.log('No active session for checking uploaded documents');
        return false;
      }
      
      const { data, error } = await supabase
        .from('user_documents')
        .select('id')
        .eq('user_id', user.id)
        .limit(1);
      
      if (error) {
        console.log('User documents table not available yet:', error.message);
        return false;
      }
      
      return data && data.length > 0;
    } catch (error) {
      console.error('Error checking uploaded documents:', error);
      return false;
    }
  };

  // Update workflow state based on current data
  useEffect(() => {
    const updateWorkflowState = async () => {
      const negativeTradelines = getNegativeTradelines();
      const { hasLetters, hasPackets } = await checkForExistingDisputePackets();
      const hasUploadedDocuments = await checkForUploadedDocuments();
      
      setWorkflowState(prev => ({
        ...prev,
        hasUploadedReports: tradelines.length > 0,
        hasSelectedTradelines: negativeTradelines.length > 0,
        hasGeneratedLetter: hasLetters,
        hasUploadedDocuments,
        hasGeneratedPacket: hasPackets,
        tradelinesCount: tradelines.length,
        negativeTradelinesCount: negativeTradelines.length,
        selectedTradelinesCount: 0, // This will be managed by individual pages
        isProfileComplete
      }));
    };

    if (user?.id) {
      updateWorkflowState();
    }
  }, [user?.id, tradelines, getNegativeTradelines, isProfileComplete]);

  // Get workflow completion status
  const getWorkflowCompletion = () => {
    const steps = [
      workflowState.hasUploadedReports,
      workflowState.hasSelectedTradelines,
      workflowState.hasGeneratedLetter,
      workflowState.hasGeneratedPacket
    ];
    
    const completedSteps = steps.filter(Boolean).length;
    const totalSteps = steps.length;
    
    return {
      completedSteps,
      totalSteps,
      percentage: Math.round((completedSteps / totalSteps) * 100),
      isComplete: completedSteps === totalSteps
    };
  };

  // Check if user can proceed to next step
  const canProceedTo = (step: 'tradelines' | 'dispute') => {
    switch (step) {
      case 'tradelines':
        return workflowState.hasUploadedReports;
      case 'dispute':
        return workflowState.hasSelectedTradelines && workflowState.isProfileComplete;
      default:
        return false;
    }
  };

  // Get step status for navigation
  const getStepStatus = (step: 'upload' | 'tradelines' | 'dispute') => {
    switch (step) {
      case 'upload':
        return {
          isCompleted: workflowState.hasUploadedReports,
          canAccess: true,
          statusText: workflowState.hasUploadedReports 
            ? `${workflowState.tradelinesCount} tradelines extracted`
            : 'Upload credit reports to begin'
        };
      case 'tradelines':
        return {
          isCompleted: workflowState.hasSelectedTradelines,
          canAccess: workflowState.hasUploadedReports,
          statusText: workflowState.hasSelectedTradelines
            ? `${workflowState.negativeTradelinesCount} negative items found`
            : workflowState.hasUploadedReports
              ? 'Select tradelines to dispute'
              : 'Upload reports first'
        };
      case 'dispute':
        return {
          isCompleted: workflowState.hasGeneratedPacket,
          canAccess: workflowState.hasSelectedTradelines && workflowState.isProfileComplete,
          statusText: workflowState.hasGeneratedPacket
            ? 'Dispute packet complete'
            : workflowState.hasGeneratedLetter
              ? 'Letters generated - finish packet'
              : workflowState.hasSelectedTradelines && workflowState.isProfileComplete
                ? 'Ready to generate dispute letters'
                : !workflowState.isProfileComplete
                  ? 'Complete profile first'
                  : 'Select tradelines first'
        };
      default:
        return { isCompleted: false, canAccess: false, statusText: '' };
    }
  };

  // Update selected tradelines count (called from Tradelines page)
  const updateSelectedTradelinesCount = (count: number) => {
    setWorkflowState(prev => ({
      ...prev,
      selectedTradelinesCount: count
    }));
  };

  return {
    workflowState,
    getWorkflowCompletion,
    canProceedTo,
    getStepStatus,
    updateSelectedTradelinesCount,
    refreshWorkflowState: () => {
      // Force re-check of workflow state
      setWorkflowState(prev => ({ ...prev }));
    }
  };
};