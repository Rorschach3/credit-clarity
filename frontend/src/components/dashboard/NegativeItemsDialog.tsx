import { useState, useEffect, useCallback } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { supabase } from "../../../supabase/client";
import { Loader2 } from "lucide-react";
import { Database } from "../../../supabase/types/supabase";


interface NegativeItemsDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

interface DisputeItem {
  id: string;
  bureau: string;
  company: string;
  type: string;
  amount: string;
  status: string;
}

interface TradelineRow {
  id: string;
  credit_bureau: string;
  letter_content: string;
  status: string;
  created_at: string;
}

export function NegativeItemsDialog({
  open,
  onOpenChange,
}: NegativeItemsDialogProps) {
  const [items, setItems] = useState<DisputeItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const fetchDisputeItems = useCallback(async () => {
    setIsLoading(true);
    try {
      const { data, error } = await supabase
        .from("disputes")
        .select("*")
        .order("created_at", { ascending: false });

      if (error) {
        console.error("Error fetching disputes:", error);
        setItems(getSampleDisputeItems());
      } else if (data && data.length > 0) {
        const mappedItems = data.map((dispute: TradelineRow) => ({
          id: dispute.id,
          bureau: dispute.credit_bureau,
          company: extractCompanyName(dispute.letter_content),
          type: "Collection Account",
          amount: "$0", // Replace with actual value if available
          status: dispute.status,
        }));
        setItems(mappedItems);
      } else {
        setItems(getSampleDisputeItems());
      }
    } catch (error) {
      console.error("Unexpected error:", error);
      setItems(getSampleDisputeItems());
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (open) {
      fetchDisputeItems();
    }
  }, [open, fetchDisputeItems]);

  function extractCompanyName(content: string): string {
    try {
      if (!content) return "Unknown Company";
      const matches = content.match(/regarding.*?account with\s+(.*?)(?:\.|,|\s+on)/i);
      return matches && matches[1] ? matches[1] : "Credit Account";
    } catch {
      return "Credit Account";
    }
  }

  function getSampleDisputeItems(): DisputeItem[] {
    return [
      {
        id: "1",
        bureau: "Experian",
        company: "Collection Agency A",
        type: "Collection Account",
        amount: "$1,245",
        status: "Pending",
      },
      {
        id: "2",
        bureau: "TransUnion",
        company: "Bank XYZ",
        type: "Late Payment",
        amount: "$89",
        status: "Disputed",
      },
      {
        id: "3",
        bureau: "Equifax",
        company: "Credit Card Company",
        type: "Charge-off",
        amount: "$3,500",
        status: "Verified",
      },
      {
        id: "4",
        bureau: "Experian",
        company: "Collection Agency B",
        type: "Collection Account",
        amount: "$567",
        status: "Removed",
      },
    ];
  }

  function getStatusBadgeVariant(status: string) {
    switch (status.toLowerCase()) {
      case "removed":
        return "bg-green-100 text-green-800 border-green-200";
      case "disputed":
      case "pending":
        return "bg-yellow-100 text-yellow-800 border-yellow-200";
      case "verified":
        return "bg-red-100 text-red-800 border-red-200";
      default:
        return "bg-gray-100 text-gray-800 border-gray-200";
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Negative Items</DialogTitle>
        </DialogHeader>

        <div className="space-y-4 mt-4 max-h-[60vh] overflow-y-auto pr-2">
          {isLoading ? (
            <div className="flex justify-center items-center py-8">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
          ) : items.length === 0 ? (
            <p className="text-center text-muted-foreground py-8">
              No negative items found.
            </p>
          ) : (
            items.map((item) => (
              <div key={item.id} className="border rounded-lg p-4 space-y-2">
                <div className="flex justify-between items-start">
                  <h4 className="font-medium">{item.company}</h4>
                  <Badge
                    variant="outline"
                    className={getStatusBadgeVariant(item.status)}
                  >
                    {item.status}
                  </Badge>
                </div>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div>
                    <span className="text-muted-foreground">Bureau:</span>{" "}
                    {item.bureau}
                  </div>
                  <div>
                    <span className="text-muted-foreground">Type:</span>{" "}
                    {item.type}
                  </div>
                  <div>
                    <span className="text-muted-foreground">Amount:</span>{" "}
                    {item.amount}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
