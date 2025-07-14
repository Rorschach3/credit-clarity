// File: src/hooks/useCreditUploadState.ts
import { useState, useCallback } from 'react';
import { toast as sonnerToast } from "sonner";
import { 
  ParsedTradeline, 
  generateUUID,
  validateParsedTradeline
} from "@/utils/tradelineParser";
import { supabase } from '@/integrations/supabase/client';

export interface UseCreditUploadStateReturn {
  tradelines: ParsedTradeline[];
  setTradelines: (tradelines: ParsedTradeline[]) => void;
  selectedTradelineIds: Set<string>;
  manualModalOpen: boolean;
  setManualModalOpen: (open: boolean) => void;
  processingMethod: 'ocr' | 'ai';
  setProcessingMethod: (method: 'ocr' | 'ai') => void;
  handleSelectTradeline: (id: string) => void;
  updateTradeline: (id: string, updates: Partial<ParsedTradeline>) => void;
  deleteTradeline: (id: string) => void;
  handleAddManual: (tradeline: Partial<ParsedTradeline>, userId: string) => Promise<void>;
  clearSelectedTradelines: () => void;
  selectAllTradelines: () => void;
  isLoading: boolean;
}

export const useCreditUploadState = (): UseCreditUploadStateReturn => {
  const [tradelines, setTradelines] = useState<ParsedTradeline[]>([]);
  const [selectedTradelineIds, setSelectedTradelineIds] = useState<Set<string>>(new Set());
  const [manualModalOpen, setManualModalOpen] = useState(false);
  const [processingMethod, setProcessingMethod] = useState<'ocr' | 'ai'>('ai');
  const [isLoading, setIsLoading] = useState(false);

  const handleSelectTradeline = useCallback((id: string) => {
    setSelectedTradelineIds(prev => {
      const newSet = new Set(prev);
      if (newSet.has(id)) {
        newSet.delete(id);
      } else {
        newSet.add(id);
      }
      return newSet;
    });
  }, []);

  const updateTradeline = useCallback((id: string, updates: Partial<ParsedTradeline>) => {
    setTradelines(prev => 
      prev.map(tradeline => 
        tradeline.id === id 
          ? { ...tradeline, ...updates }
          : tradeline
      )
    );
  }, []);

  // Fixed: was using user_id instead of id
  const deleteTradeline = useCallback(async (id: string) => {
    try {
      setIsLoading(true);
      
      // Remove from database
      const { error } = await supabase
        .from('tradelines')
        .delete()
        .eq('id', id);

      if (error) {
        console.error('[ERROR] Failed to delete tradeline from database:', error);
        sonnerToast('Failed to delete tradeline from database', { 
          description: error.message 
        });
        return;
      }

      // Remove from local state
      setTradelines(prev => prev.filter(tradeline => tradeline.id !== id));
      setSelectedTradelineIds(prev => {
        const newSet = new Set(prev);
        newSet.delete(id);
        return newSet;
      });
      
      sonnerToast('Tradeline deleted successfully', { 
        description: 'The tradeline has been removed from your account' 
      });
      
    } catch (error) {
      console.error('[ERROR] Exception deleting tradeline:', error);
      sonnerToast('Failed to delete tradeline', { 
        description: error instanceof Error ? error.message : 'Unknown error' 
      });
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Fixed: proper UUID generation and database saving
  const handleAddManual = useCallback(async (
    tradelineData: Partial<ParsedTradeline>, 
    authUserId: string
  ) => {
    try {
      setIsLoading(true);
      console.log('[DEBUG] 📝 Adding manual tradeline for user:', authUserId);


      // Create complete tradeline with proper UUID
      const completeTradeline: ParsedTradeline = {
        id: generateUUID(), // Use proper UUID generator
        user_id: authUserId,
        creditor_name: tradelineData.creditor_name || '',
        account_number: tradelineData.account_number || '',
        account_balance: tradelineData.account_balance || '$0',
        account_status: tradelineData.account_status || '',
        account_type: tradelineData.account_type || '',
        date_opened: tradelineData.date_opened || '',
        is_negative: tradelineData.is_negative || false,
        credit_bureau: tradelineData.credit_bureau || 'Unknown',
        dispute_count: tradelineData.dispute_count || 0,
        created_at: new Date().toISOString(),
        ...tradelineData // Override with any provided data
      };

      // Validate the tradelined
      const validation = validateParsedTradeline(completeTradeline);
      if (!validation.success) {
        throw new Error(`Invalid tradeline data: ${validation.error}`);
      }

      // Save to database
      const { data, error } = await supabase
        .from('tradelines')
        .insert({
          id: completeTradeline.id,
          user_id: completeTradeline.user_id,
          creditor_name: completeTradeline.creditor_name,
          account_number: completeTradeline.account_number,
          account_type: completeTradeline.account_type,
          account_status: completeTradeline.account_status,
          account_balance: completeTradeline.account_balance,
          date_opened: completeTradeline.date_opened,
          credit_bureau: completeTradeline.credit_bureau,
          is_negative: completeTradeline.is_negative,
          dispute_count: completeTradeline.dispute_count,
        })
        .select()
        .single();

      if (error) {
        console.error('[ERROR] Failed to save manual tradeline:', error);
        throw new Error(`Database error: ${error.message}`);
      }

      // Add to local state
      setTradelines(prev => [...prev, completeTradeline]);
      setManualModalOpen(false);
      
      console.log('[SUCCESS] ✅ Manual tradeline added:', data?.id);
      sonnerToast('Manual tradeline added successfully', { 
        description: `Added ${completeTradeline.creditor_name} to your credit profile` 
      });
      
    } catch (error) {
      console.error('[ERROR] Exception adding manual tradeline:', error);
      const errorMessage = error instanceof Error ? error.message : 'Failed to add tradeline';
      sonnerToast(errorMessage, { 
        description: 'Please check your input and try again' 
      });
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const clearSelectedTradelines = useCallback(() => {
    setSelectedTradelineIds(new Set());
  }, []);

  const selectAllTradelines = useCallback(() => {
    const allIds = new Set(tradelines.map(t => t.id).filter(Boolean) as string[]);
    setSelectedTradelineIds(allIds);
  }, [tradelines]);

  return {
    tradelines,
    setTradelines,
    selectedTradelineIds,
    manualModalOpen,
    setManualModalOpen,
    processingMethod,
    setProcessingMethod,
    handleSelectTradeline,
    updateTradeline,
    deleteTradeline,
    handleAddManual,
    clearSelectedTradelines,
    selectAllTradelines,
    isLoading,
  };
};