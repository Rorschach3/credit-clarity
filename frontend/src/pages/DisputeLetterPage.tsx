"use client";

import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { toast } from "@/components/ui/use-toast";
import MainLayout from "@/components/layout/MainLayout";
import { useAuth } from "@/hooks/use-auth";
import { ParsedTradeline, fetchUserTradelines } from "@/utils/tradelineParser";
import { UserInfoForm } from "@/components/disputes/UserInfoForm";
import {LetterEditor} from "@/components/disputes/LetterEditor";
import { TradelineList } from "@/components/disputes/TradelineList";

const DisputeLetterPage = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [tradelines, setTradelines] = useState<ParsedTradeline[]>([]);
  const [selectedTradelines, setSelectedTradelines] = useState<ParsedTradeline[]>([]);
  const [userInfo, setUserInfo] = useState({ name: "", address: "", city: "", state: "", zip: "" });
  const [letter, setLetter] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) {
      toast({ title: "Error", description: "User not authenticated." });
      navigate("/login");
      return;
    }

    const loadData = async () => {
      setLoading(true);
      try {
        // Fetch tradelines for user from Supabase
        const userTradelines = await fetchUserTradelines(user.id);
        setTradelines(userTradelines);

        // Autofill user info from Supabase profile (assuming user profile data available)
        // For now, set dummy or empty values; replace with actual fetch if available
        setUserInfo({
          name: user.email || "",
          address: "",
          city: "",
          state: "",
          zip: "",
        });
      } catch (error) {
        toast({ title: "Error", description: "Failed to load tradelines or user info." });
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [user, navigate]);

  const handleProceed = () => {
    // Navigate to dispute packet page
    navigate("/dispute-packet");
  };

  // Only allow selection of negative tradelines
  const Tradelines = tradelines.filter((t) => t.isNegative);

  return (
   <MainLayout>
    <div className="min-h-screen bg-background text-foreground py-10 px-4 md:px-10">
     <Card className="max-w-6xl mx-auto space-y-6">
      <CardHeader>
          <CardTitle className="text-2xl">Step 2: Draft Dispute Letter</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          {loading ? (
            <p>Loading...</p>
          ) : (
            <>
              <TradelineList
                tradelines={tradelines}
                selected={selectedTradelines}
                setSelected={setSelectedTradelines}
                onAddManual={() => toast({ title: "Info", description: "Manual add not available here." })}
              />

              <UserInfoForm userInfo={userInfo} onChange={setUserInfo} />

              <LetterEditor
                userInfo={userInfo}
                selectedTradelines={selectedTradelines}
                letter={letter}
                setLetter={setLetter}
                setShowDocsSection={() => {}}
              />

              <div className="flex justify-end space-x-4">
                <Button onClick={handleProceed} disabled={selectedTradelines.length === 0}>
                  Proceed to Step 3
                </Button>
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </div>
   </MainLayout>
  );
};

export default DisputeLetterPage;