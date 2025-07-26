import { Button } from "@/components/ui/button";
import { useState } from "react";
import { toast } from "@/components/ui/use-toast";

interface Props {
  letterText: string;
  toName: string;
  toAddress: {
    line1: string;
    city: string;
    state: string;
    zip: string;
  };
}

export function SendDisputeLetterButton({ letterText, toName, toAddress }: Props) {
  const [loading, setLoading] = useState(false);

  const handleSend = async () => {
    setLoading(true);
    try {
      const response = await fetch("/functions/send-letter", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          to: {
            name: toName,
            address_line1: toAddress.line1,
            address_city: toAddress.city,
            address_state: toAddress.state,
            address_zip: toAddress.zip,
          },
          body: letterText,
        }),
      });

      if (!response.ok) throw new Error("Failed to send letter");

      const result = await response.json();
      toast({
        title: "Letter Sent",
        description: `Mail ID: ${result.lob_id}`,
      });
    } catch (err) {
      console.error(err);
      toast({
        title: "Send Failed",
        description: "There was an error sending the letter.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Button onClick={handleSend} disabled={loading}>
      {loading ? "Sending..." : "Send via Mail"}
    </Button>
  );
}
