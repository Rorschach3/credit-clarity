
import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import type { NegativeItem } from "@/types/document";
import { DisputeAnalysis } from "@/utils/ai-service";
import { NegativeItemCard } from "./negative-items/NegativeItemCard";
import { AiHeader } from "./negative-items/AiHeader";
import { AiAlert } from "./negative-items/AiAlert";
import { ListActions } from "./negative-items/ListActions";

interface EnhancedNegativeItemsListProps {
  items: NegativeItem[];
  analysis?: DisputeAnalysis;
  onGenerateDisputes: (items: NegativeItem[]) => void;
}

export function EnhancedNegativeItemsList({ 
  items, 
  analysis,
  onGenerateDisputes 
}: EnhancedNegativeItemsListProps) {
  const [selectedItems, setSelectedItems] = useState<Record<string, boolean>>({});
  const [showRecommendationsOnly, setShowRecommendationsOnly] = useState(false);

  // Initialize with AI recommendations if available
  useEffect(() => {
    if (analysis?.recommendedDisputes) {
      const initialSelected: Record<string, boolean> = {};
      analysis.recommendedDisputes.forEach(item => {
        initialSelected[item.id] = true;
      });
      setSelectedItems(initialSelected);
    }
  }, [analysis]);

  const toggleItem = (itemId: string) => {
    setSelectedItems(prev => ({
      ...prev,
      [itemId]: !prev[itemId]
    }));
  };

  const handleGenerateDisputes = () => {
    const itemsToDispute = items.filter(item => selectedItems[item.id]);
    onGenerateDisputes(itemsToDispute);
  };

  const getRecommendedReason = (itemId: string) => {
    if (!analysis?.recommendedDisputes) return null;
    
    const recommendedItem = analysis.recommendedDisputes.find(item => item.id === itemId);
    return recommendedItem?.recommendedReason || null;
  };

  const selectedCount = Object.values(selectedItems).filter(Boolean).length;
  
  // Filter items based on recommendations if filter is active
  const displayedItems = showRecommendationsOnly && analysis
    ? items.filter(item => 
        analysis.recommendedDisputes.some(rec => rec.id === item.id)
      )
    : items;

  if (items.length === 0) {
    return null;
  }

  const hasRecommendations = analysis?.recommendedDisputes && analysis.recommendedDisputes.length > 0;

  return (
    <Card className="w-full mt-6">
      <CardHeader>
        <AiHeader 
          hasAiAnalysis={!!analysis}
          showRecommendationsOnly={showRecommendationsOnly}
          hasRecommendations={hasRecommendations}
          onToggleRecommendations={() => setShowRecommendationsOnly(!showRecommendationsOnly)}
        />
      </CardHeader>
      <CardContent>
        {analysis && (
          <AiAlert recommendationsCount={analysis.recommendedDisputes.length} />
        )}

        <div className="space-y-4">
          {displayedItems.map((item) => {
            const isAiRecommended = analysis?.recommendedDisputes?.some(rec => rec.id === item.id);
            const recommendedReason = getRecommendedReason(item.id);
            
            return (
              <NegativeItemCard 
                key={item.id}
                item={item}
                isSelected={!!selectedItems[item.id]}
                isAiRecommended={!!isAiRecommended}
                recommendedReason={recommendedReason}
                onToggleSelect={toggleItem}
              />
            );
          })}
          
          <ListActions 
            selectedCount={selectedCount}
            totalCount={items.length}
            onGenerateDisputes={handleGenerateDisputes}
          />
        </div>
      </CardContent>
    </Card>
  );
}
