
import { useState } from "react";
import { Checkbox } from "@/components/ui/checkbox";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { type NegativeItem } from "@/types/negative-item";

interface NegativeItemsListProps {
  items: NegativeItem[];
  onGenerateDisputes: (items: NegativeItem[]) => void;
}

export function NegativeItemsList({ items, onGenerateDisputes }: NegativeItemsListProps) {
  const [selectedItems, setSelectedItems] = useState<Record<string, boolean>>({});

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

  const selectedCount = Object.values(selectedItems).filter(Boolean).length;

  if (items.length === 0) {
    return null;
  }

  return (
    <Card className="w-full mt-6">
      <CardHeader>
        <CardTitle>Negative Items Found</CardTitle>
        <CardDescription>
          Select the items you want to dispute on your credit report
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {items.map((item) => (
            <div 
              key={item.id} 
              className={`flex items-start p-4 rounded-lg border ${
                selectedItems[item.id] ? 'border-primary bg-primary/5' : 'border-gray-200'
              }`}
            >
              <Checkbox 
                id={`item-${item.id}`}
                checked={!!selectedItems[item.id]}
                onCheckedChange={() => toggleItem(item.id)}
                className="mt-1 mr-3"
              />
              <div className="flex-1">
                <div className="flex flex-wrap justify-between gap-2 mb-2">
                  <div>
                    <label 
                      htmlFor={`item-${item.id}`}
                      className="font-medium cursor-pointer"
                    >
                      {item.creditorName}
                    </label>
                    <p className="text-sm text-muted-foreground">
                      Account: {item.accountNumber}
                    </p>
                  </div>
                  <Badge variant="outline" className="text-red-500 border-red-200 bg-[rgba(255,255,255,0.08)]">
                    {item.reason}
                  </Badge>
                </div>

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
                      {item.bureaus.map((bureau: string) => (
                        <Badge key={bureau} variant="secondary" className="text-xs">
                          {bureau}
                        </Badge>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))}
          
          <div className="flex justify-between items-center mt-6 pt-4 border-t">
            <p className="text-sm text-muted-foreground">
              {selectedCount} of {items.length} items selected
            </p>
            <Button 
              onClick={handleGenerateDisputes}
              disabled={selectedCount === 0}
            >
              Generate Dispute Letters
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
