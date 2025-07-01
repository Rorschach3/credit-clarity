import { Checkbox } from "@/components/ui/checkbox";
import { Badge } from "@/components/ui/badge";
import { Info, Bot } from "lucide-react";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import type { NegativeItem } from "@/types/negative-item";

interface NegativeItemCardProps {
  item: NegativeItem;
  isSelected: boolean;
  isAiRecommended: boolean;
  recommendedReason: string | null;
  onToggleSelect: (itemId: string) => void;
}

export function NegativeItemCard({ 
  item, 
  isSelected, 
  isAiRecommended, 
  recommendedReason,
  onToggleSelect 
}: NegativeItemCardProps) {
  return (
    <div 
      className={`flex items-start p-4 rounded-lg border ${
        isSelected 
          ? 'border-primary bg-primary/5' 
          : isAiRecommended 
            ? 'border-blue-200 bg-blue-50/30'
            : 'border-gray-200'
      }`}
    >
      <Checkbox 
        id={`item-${item.id}`}
        checked={isSelected}
        onCheckedChange={() => onToggleSelect(item.id)}
        className="mt-1 mr-3"
      />
      <div className="flex-1">
        <div className="flex flex-wrap justify-between gap-2 mb-2">
          <div className="flex items-center">
            <label 
              htmlFor={`item-${item.id}`}
              className="font-medium cursor-pointer"
            >
              {item.creditorName}
            </label>
            {isAiRecommended && (
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Badge className="ml-2 bg-blue-100 text-blue-800 border-blue-200 flex items-center">
                      <Bot className="h-3 w-3 mr-1" />
                      AI Recommended
                    </Badge>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p className="max-w-xs text-sm">
                      Our AI system recommends disputing this item because it has a high likelihood of success.
                    </p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            )}
          </div>
          <Badge variant="outline" className="text-red-500 border-red-200 bg-[rgba(255,255,255,0.08)]">
            {item.reason}
          </Badge>
        </div>

        <p className="text-sm text-muted-foreground">
          Account: {item.accountNumber}
        </p>

        {recommendedReason && (
          <div className="mt-2 flex items-start gap-2 text-sm border-t border-blue-100 pt-2">
            <Info className="h-4 w-4 text-blue-500 mt-0.5 flex-shrink-0" />
            <div>
              <span className="font-medium text-blue-700">AI Recommended Dispute Reason: </span>
              <span>{recommendedReason}</span>
            </div>
          </div>
        )}

        <div className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm mt-2">
          <div>
            <span className="text-muted-foreground">Amount:</span> {item.amount}
          </div>
          <div>
            <span className="text-muted-foreground">Date Reported:</span> {item.dateReported}
          </div>
          <div className="col-span-2">
            <span className="text-muted-foreground">Bureaus:</span>{" "}
            <div className="inline-flex flex-wrap gap-1 mt-1">
              {item.bureaus.map(bureau => (
                <Badge key={bureau} variant="secondary" className="text-xs">
                  {bureau}
                </Badge>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
