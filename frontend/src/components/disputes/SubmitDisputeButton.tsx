import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { toast } from "@/components/ui/use-toast";
import { supabase } from "../../supabase/client";
import { useState } from "react";

interface SubmitDisputeButtonProps {
  letterId: string;
  userEmail: string;
  userName: string;
}

export function SubmitDisputeButton({ letterId, userEmail, userName }: SubmitDisputeButtonProps) {
  const [submitting, setSubmitting] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async () => {
    setSubmitting(true);
    try {
      // ✅ Update dispute_letter status
      const { error } = await supabase
        .from("disputes")
        .update({
          status: "submitted",
          submitted_at: new Date().toISOString(),
        })
        .eq("id", letterId);

      if (error) throw error;

      // ✅ Trigger Resend confirmation email
      const emailRes = await fetch("/functions/send-confirmation-email", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          to: userEmail,
          name: userName || "there",
        }),
      });

      if (!emailRes.ok) {
        const msg = await emailRes.text();
        console.error("Email error:", msg);
      }

      toast({ title: "Dispute Submitted", description: "Confirmation email sent." });
      navigate("/dispute-confirmation");
    } catch (err) {
      console.error("Submission error:", err);
      toast({
        title: "Submission Failed",
        description: "Could not finalize the dispute.",
        variant: "destructive",
      });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Button onClick={handleSubmit} disabled={submitting}>
      {submitting ? "Submitting..." : "Submit Dispute Packet"}
    </Button>
  );
}
