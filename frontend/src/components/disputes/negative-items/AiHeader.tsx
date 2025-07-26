
import { Bot } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

interface AiHeaderProps {
  hasAiAnalysis: boolean;
  showRecommendationsOnly: boolean;
  hasRecommendations: boolean;
  onToggleRecommendations: () => void;
}

export function AiHeader({ 
  hasAiAnalysis,
  showRecommendationsOnly,
  hasRecommendations,
  onToggleRecommendations
}: AiHeaderProps) {
  return (
    <div className="flex items-center justify-between">
      <div>
        <CardTitle className="flex items-center gap-2">
          Negative Items Found
          {hasAiAnalysis && (
            <Badge variant="outline" className="bg-blue-100 text-blue-800 ml-2">
              <Bot className="h-3 w-3 mr-1" />
              AI Enhanced
            </Badge>
          )}
        </CardTitle>
        <CardDescription>
          Select the items you want to dispute on your credit report
        </CardDescription>
      </div>
      
      {hasRecommendations && (
        <Button
          variant="outline"
          size="sm"
          onClick={onToggleRecommendations}
          className="text-xs h-8"
        >
          {showRecommendationsOnly ? "Show All Items" : "Show AI Recommendations Only"}
        </Button>
      )}
    </div>
  );
}
