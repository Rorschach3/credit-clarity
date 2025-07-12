import { useState, useCallback } from 'react';
import { toast as sonnerToast } from "sonner";
import { ParsedTradeline } from "@/utils/tradelineParser"; // Fixed import

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
  handleAddManual: (tradeline: ParsedTradeline, userId: string) => Promise<void>;
  clearSelectedTradelines: () => void;
  selectAllTradelines: () => void;
}

export const useCreditUploadState = (): UseCreditUploadStateReturn => {
  const [tradelines, setTradelines] = useState<ParsedTradeline[]>([]);
  const [selectedTradelineIds, setSelectedTradelineIds] = useState<Set<string>>(new Set());
  const [manualModalOpen, setManualModalOpen] = useState(false);
  const [processingMethod, setProcessingMethod] = useState<'ocr' | 'ai'>('ai');

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

  const deleteTradeline = useCallback((id: string) => {
    setTradelines(prev => prev.filter(tradeline => tradeline.id !== id));
    setSelectedTradelineIds(prev => {
      const newSet = new Set(prev);
      newSet.delete(id);
      return newSet;
    });
  }, []);

  const handleAddManual = useCallback(async (tradeline: ParsedTradeline, userId: string) => {
    try {
      // Ensure the tradeline has required fields
      const completeTraceline: ParsedTradeline = {
        ...tradeline,
        id: tradeline.id || `manual-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        user_id: tradeline.user_id || userId,
        created_at: tradeline.created_at || new Date().toISOString(),
      };

      setTradelines(prev => [...prev, completeTraceline]);
      setManualModalOpen(false);
      
      sonnerToast("Manual tradeline added successfully.", { description: "Success" });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to add tradeline';
      sonnerToast(errorMessage, { description: "Error" });
      throw error;
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
  };
};