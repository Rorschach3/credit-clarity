"use client";

import React, { useEffect, useState } from "react";
import { supabase } from "../../supabase/client";
import { Database } from "../../supabase/types/supabase";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import MainLayout from "@/components/layout/MainLayout";
import { toast } from "@/components/ui/use-toast";
import { DocumentUploadSection } from "@/components/disputes/DocumentUploadSection";
import { MailingInstructions } from "@/components/disputes/MailingInstructions";
import { UserInfoForm } from "@/components/disputes/UserInfoForm";
import { DisputeWizardStep2SelectTradelines } from "@/components/disputes/DisputeWizardStep2SelectTradelines";
import { ManualTradelineModal } from "@/components/disputes/ManualTradelineModal";
import { generateDisputePacketPdf } from "@/utils/generateDisputePacketPdf";
import { uploadDisputePacket } from "@/utils/uploadDisputePacket";
import { SubmitDisputeButton } from "@/components/disputes/SubmitDisputeButton";


const DisputePacketPage: React.FC = () => {
  const [userId, setUserId] = useState<string | null>(null);
  const [userEmail, setUserEmail] = useState<string>("");
  const [letterId, setLetterId] = useState<string | null>(null);
  const [uploadedDocs, setUploadedDocs] = useState<File[]>([]);
  const [selectedTradelines, setSelectedTradelines] = useState<Tradeline[]>([]);
  const [userInfo, setUserInfo] = useState({
    name: "",
    address: "",
    city: "",
    state: "",
    zip: "",
    email: ""
  });
  const [showDocsSection, setShowDocsSection] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [generating, setGenerating] = useState(false);
      const user = authData?.user;
      if (!user) return;

      setUserId(user.id);
      setUserEmail(user.email ?? "");

      // Fetch latest letter
      const { data: letters } = await supabase
        .from("disputes")
      // Fetch latest letter
      const { data: letters } = await supabase
        .from("disputes")
        .select("id, mailing_address")
        .eq("user_id", user.id)
        .order("created_at", { ascending: false })
        .limit(1);

      if (letters && letters.length > 0) {
        setLetterId(letters[0].id);
      }
      setUploadedDocs(files);
    };

    fetchInitialData();
  }, []);
  const handleGeneratePacket = async () => {
    setGenerating(true);
    try {
      if (!userId) throw new Error("User not authenticated");

      const [firstName, ...last] = userInfo.name.trim().split(" ");
      const letterContent = JSON.stringify({
        firstName,
        lastName: last.join(" "),
        address: userInfo.address,
        city: userInfo.city,
        state: userInfo.state,
        zip: userInfo.zip,
        tradelines: selectedTradelines.map((t) => ({
          creditorName: t.creditorName || "",
          accountNumber: t.accountNumber || "",
          accountStatus: t.accountStatus || "",
          negativeReason: t.negativeReason || "",
        })),
      });

      const { data, error } = await supabase
      const [firstName, ...last] = userInfo.name.trim().split(" ");

      const { data, error } = await supabase
        .from("disputes")
        .insert({
          user_id: userId,
          email: userInfo.email || userEmail,
          mailing_address: `${userInfo.address}\n${userInfo.city}, ${userInfo.state} ${userInfo.zip}`,
          status: 'pending'
        })
        .select("id")
        .single();

      toast({
        title: "Packet Download Ready",
        description: "Your dispute packet was successfully generated.",
      });
    } catch (error: unknown) {
      console.error("Error generating packet:", error);
      let errorMessage = "Please try again.";
      if (error instanceof Error) {
        errorMessage = error.message;
      }
      toast({
        title: "Generation Failed",
        description: errorMessage,
        variant: "destructive",
      });
      setGenerating(false);
    }
  };
  return (
    <MainLayout>
      <div className="min-h-screen bg-background text-foreground py-10 px-4 md:px-10">
        <Card className="max-w-6xl mx-auto space-y-6">
          <CardHeader>
            <CardTitle className="text-2xl">Step 3: Generate Dispute Packet</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <p>Would you like to add your identity documents to this dispute?</p>

            {!showDocsSection && (
              <Button onClick={() => setShowDocsSection(true)}>
                Add Identity Documents
              </Button>
            )}

            {showDocsSection && (
              <DocumentUploadSection onClose={() => setShowDocsSection(false)} />
            )}

            <MailingInstructions />

            <UserInfoForm userInfo={userInfo} onChange={(data) => setUserInfo(prev => ({ ...prev, ...data }))} />

            <DisputeWizardStep2SelectTradelines
              tradelines={selectedTradelines}
              selectedTradelines={selectedTradelines}
              onSelectionChange={setSelectedTradelines}
              onEditTradeline={(t) =>
                setSelectedTradelines((prev) =>
                  prev.map((p) =>
                    p.accountNumber === t.accountNumber ? t : p
                  )
                )
              }
              onDeleteTradeline={(accountNumber) =>
                setSelectedTradelines((prev) =>
                  prev.filter((t) => t.accountNumber !== accountNumber)
                )
              }
              onAddManualTradeline={() => setIsModalOpen(true)}
            />

            <Button onClick={handleGeneratePacket} disabled={generating}>
              {generating ? "Generating..." : "Generate Dispute Packet"}
            </Button>

            {letterId && userEmail && (
              <SubmitDisputeButton
                letterId={letterId}
                userEmail={userEmail}
                userName={userInfo.name}
              />
            )}
          </CardContent>
        </Card>
      </div>

      {isModalOpen && (
        <ManualTradelineModal
            <DisputeWizardStep2SelectTradelines
              tradelines={selectedTradelines}
              selectedTradelines={selectedTradelines}
              onSelectionChange={(selected) => setSelectedTradelines(selected.map(t => ({
                ...t,
                accountBalance: typeof t.accountBalance === 'string' ? parseFloat(t.accountBalance) || 0 : t.accountBalance
              })))}
              onEditTradeline={(t) =>
                setSelectedTradelines((prev) =>
                  prev.map((p) =>
                    p.accountNumber === t.accountNumber ? {
                      ...t,
                      accountBalance: typeof t.accountBalance === 'string' ? parseFloat(t.accountBalance) || 0 : t.accountBalance
                    } : p
                  )
                )
              }
              onDeleteTradeline={(accountNumber) =>
                setSelectedTradelines((prev) =>
                  prev.filter((t) => t.accountNumber !== accountNumber)
                )
              }
              onAddManualTradeline={() => setIsModalOpen(true)}
            />
      {isModalOpen && (
        <ManualTradelineModal
          onClose={() => setIsModalOpen(false)}
          onAdd={(tradeline) =>
            setSelectedTradelines((prev) => [...prev, {
              ...tradeline,
              accountBalance: typeof tradeline.accountBalance === 'string' ? parseFloat(tradeline.accountBalance) || 0 : tradeline.accountBalance
            }])
          }
        />
      )}
