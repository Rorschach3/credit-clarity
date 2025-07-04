"use client";

import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { toast } from "@/components/ui/use-toast";
import { DocumentUploadSection } from "@/components/disputes/DocumentUploadSection";
import { MailingInstructions } from "@/components/disputes/MailingInstructions";
import { CreditNavbar } from "@/components/navbar/CreditNavbar";

const DisputePacketPage = () => {
  const [showDocsSection, setShowDocsSection] = useState(false);

  const handleGeneratePacket = () => {
    // Logic to combine uploaded documents and generate the dispute packet
    toast({ title: "Packet Generated", description: "Dispute packet generated successfully!" });
  };

  return (
    <div className="min-h-screen bg-background text-foreground py-10 px-4 md:px-10">
      <CreditNavbar />
      <Card className="max-w-6xl mx-auto space-y-6">
        <CardHeader>
          <CardTitle className="text-2xl">Step 3: Generate Dispute Packet</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <p>
            Would you like to add your identity documents to this dispute?
          </p>

          <Button onClick={() => setShowDocsSection(true)}>
            Add Identity Documents
          </Button>

          {showDocsSection && (
            <DocumentUploadSection onClose={() => setShowDocsSection(false)} />
          )}

          <MailingInstructions />

          <Button onClick={handleGeneratePacket}>
            Generate Dispute Packet
          </Button>
        </CardContent>
      </Card>
    </div>
  );
};

export default DisputePacketPage;