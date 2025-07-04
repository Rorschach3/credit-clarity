
import { useState, useCallback } from 'react';
import { ParsedTradeline } from "@/utils/tradelineParser";

export const useCreditUploadState = () => {
  const [tradelines, setTradelines] = useState<ParsedTradeline[]>([]);
  const [selectedTradelineIds, setSelectedTradelineIds] = useState<Set<string>>(new Set());
  const [manualModalOpen, setManualModalOpen] = useState(false);
  const [processingMethod, setProcessingMethod] = useState<'ocr' | 'ai'>('ai');
  const [showAiResults, setShowAiResults] = useState(false);

  const handleSelectTradeline = useCallback((id: string, isSelected: boolean) => {
    setSelectedTradelineIds(prev => {
      const newSet = new Set(prev);
      if (isSelected) {
        newSet.add(id);
      } else {
        newSet.delete(id);
      }
      return newSet;
    });
  }, []);

  const updateTradeline = useCallback((index: number, updated: Partial<ParsedTradeline>) => {
    setTradelines((prev) => {
      const newTradelines = [...prev];
      newTradelines[index] = { ...newTradelines[index], ...updated };
      console.log("Updated tradeline:", newTradelines[index]);
      return newTradelines;
    });
  }, []);

  const deleteTradeline = useCallback((index: number) => {
    setTradelines((prev) => prev.filter((_, i) => i !== index));
  }, []);

  const handleAddManual = useCallback((newTradeline: ParsedTradeline, userId: string) => {
    const tradelineWithUserId = {
      ...newTradeline,
      user_id: userId
    };
    setTradelines(prev => [...prev, tradelineWithUserId]);
    setManualModalOpen(false);
  }, []);

  return {
    tradelines,
    setTradelines,
    selectedTradelineIds,
    manualModalOpen,
    setManualModalOpen,
    processingMethod,
    setProcessingMethod,
    showAiResults,
    setShowAiResults,
    handleSelectTradeline,
    updateTradeline,
    deleteTradeline,
    handleAddManual
  };
};
