import { useState, useEffect, useCallback } from "react";
import { differenceInCalendarDays, addBusinessDays } from "date-fns";
import { useToast } from "@/hooks/use-toast";
import { supabase } from "../../../supabase/client";
import useActivityMonitoring from "@/hooks/use-activity-monitoring";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Printer, Loader2 } from "lucide-react";
import RealTimeQueue from "./RealTimeQueue";
import type { Database } from "@/integrations/supabase/types";

// Derive the exact row type from your Supabase schema
type Dispute = Database["public"]["Tables"]["disputes"]["Row"];

export interface DisputeManagementProps {
  isLoading: boolean;
  disputes: Dispute[];
  fetchDisputes: () => Promise<void>;
  setDisputes: React.Dispatch<React.SetStateAction<Dispute[]>>;
}

export const DisputeManagement: React.FC<DisputeManagementProps> = ({
  isLoading,
  disputes,
  fetchDisputes,
  setDisputes,
}) => {
  const toast = useToast();
  const [processing, setProcessing] = useState<Record<string, boolean>>({});
  const [escalationThreshold] = useState<number>(35);

  useActivityMonitoring("Viewed Dispute Management");

  // Generate shipping label via Edge Function
  const generateShippingLabel = useCallback(async (dispute: Dispute) => {
    setProcessing((p) => ({ ...p, [dispute.id]: true }));
    try {
      if (!dispute.mailing_address) throw new Error("Missing mailing address");

      const [line1, line2 = ""] = dispute.mailing_address.split("\n");
      const [cityPart = "", stateZipPart = ""] = line2.split(",");
      const city = cityPart.trim();
      const [state = "", zip = ""] = stateZipPart.trim().split(" ");

      const response = await supabase.functions.invoke("generate-shipping-label", {
        body: {
          disputeId: dispute.id,
          toAddress: {
            name: dispute.credit_bureau,
            street1: line1,
            city,
            state,
            zip,
            country: "US",
          },
        },
      });

      if (response.error) throw new Error(response.error.message);

      const { error: updateError } = await supabase
        .from<"disputes", Dispute>("disputes")
        .update({ lob_id: response.data.labelUrl, status: "label_generated" })
        .eq("id", dispute.id);

      if (updateError) throw updateError;

      toast({ title: "Success", description: "Shipping label generated." });
      await fetchDisputes();
    } catch (err) {
      console.error(err);
      const message = err instanceof Error ? err.message : "Failed to generate label";
      toast({ title: "Error", description: message, variant: "destructive" });
    } finally {
      setProcessing((p) => ({ ...p, [dispute.id]: false }));
    }
  }, [fetchDisputes, toast]);

  // Mark dispute as sent
  const markAsSent = useCallback(async (dispute: Dispute) => {
    setProcessing((p) => ({ ...p, [dispute.id]: true }));
    try {
      const { error } = await supabase
        .from<"disputes", Dispute>("disputes")
        .update({ status: "sent" })
        .eq("id", dispute.id);
      if (error) throw error;

      toast({ title: "Success", description: "Marked as sent." });
      await fetchDisputes();
    } catch (err) {
      console.error(err);
      const message = err instanceof Error ? err.message : "Failed to update status";
      toast({ title: "Error", description: message, variant: "destructive" });
    } finally {
      setProcessing((p) => ({ ...p, [dispute.id]: false }));
    }
  }, [fetchDisputes, toast]);

  // Check and log FCRA deadlines hourly
  useEffect(() => {
    const checkDeadlines = () => {
      const nearing = disputes.filter(
        (d) => differenceInCalendarDays(new Date(), new Date(d.created_at)) >= 40
      );
      if (nearing.length) console.log(
        `${nearing.length} disputes nearing 40-day FCRA deadline`
      );
    };
    checkDeadlines();
    const iv = setInterval(checkDeadlines, 60 * 60 * 1000);
    return () => clearInterval(iv);
  }, [disputes]);

  // Auto-escalate stale disputes
  useEffect(() => {
    const escalate = async () => {
      const toEsc = disputes.filter(
        (d) => d.status === "processing" &&
          differenceInCalendarDays(new Date(), new Date(d.created_at)) >= escalationThreshold
      );
      for (const d of toEsc) {
        await supabase
          .from<"disputes", Dispute>("disputes")
          .update({ status: "escalated" }).eq("id", d.id);
      }
      if (toEsc.length) {
        setDisputes((prev) => prev.map((d) =>
          toEsc.some((e) => e.id === d.id) ? { ...d, status: "escalated" } : d
        ));
      }
    };
    void escalate();
  }, [disputes, escalationThreshold, setDisputes]);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Dispute Management</CardTitle>
        <CardDescription>
          <Badge variant="outline" className="border-blue-200 text-blue-600">
            FCRA §611
          </Badge>
          &nbsp;Manage dispute letters & shipments
        </CardDescription>
      </CardHeader>
      <CardContent>
        <RealTimeQueue />
        <div className="mt-4 overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Credit Bureau</TableHead>
                <TableHead>Created</TableHead>
                <TableHead>Violations</TableHead>
                <TableHead>Deadline</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={6} className="text-center py-8">
                    <Loader2 className="animate-spin mr-2 inline-block" /> Loading…
                  </TableCell>
                </TableRow>
              ) : disputes.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} className="text-center py-8">
                    No disputes found.
                  </TableCell>
                </TableRow>
              ) : (
                disputes.map((d) => {
                  const createdDate = new Date(d.created_at);
                  const deadline = addBusinessDays(createdDate, 30);
                  return (
                    <TableRow key={d.id}>
                      <TableCell>{d.credit_bureau}</TableCell>
                      <TableCell>{createdDate.toLocaleDateString()}</TableCell>
                      <TableCell>
                        {d.fcra_violations?.split(",").map((v) => (
                          <Badge key={v} variant="destructive" className="mr-1">
                            {v}
                          </Badge>
                        ))}
                      </TableCell>
                      <TableCell className={
                        differenceInCalendarDays(new Date(), createdDate) > 40 ?
                          "text-red-600 font-medium" : ""
                      }>
                        {deadline.toLocaleDateString()}
                      </TableCell>
                      <TableCell>
                        <Badge variant={
                          d.status === "escalated" ? "destructive" : "outline"
                        }>
                          {d.status}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className="flex space-x-2">
                          <Button
                            size="sm"
                            onClick={() => void generateShippingLabel(d)}
                            disabled={!!processing[d.id]}
                          >
                            <Printer className="h-4 w-4" /> Label
                          </Button>
                          {d.lob_id && (
                            <a
                              href={d.lob_id}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="inline-flex items-center"
                            >
                              View Label
                            </a>
                          )}
                          <Button
                            size="sm"
                            onClick={() => void markAsSent(d)}
                            disabled={!!processing[d.id]}
                          >
                            Mark Sent
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  );
                })
              )}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  );
};
