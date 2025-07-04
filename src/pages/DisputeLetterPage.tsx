
"use client";

import React, { useState, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { toast } from "@/components/ui/use-toast";
import MainLayout from "@/components/layout/MainLayout";
import { useAuth } from "@/hooks/use-auth";
import { ParsedTradeline, fetchUserTradelines } from "@/utils/tradelineParser";
import { UserInfoForm } from "@/components/disputes/UserInfoForm";
import { LetterEditor } from "@/components/disputes/LetterEditor";
import { TradelineList } from "@/components/disputes/TradelineList";

interface LocationState {
  selectedTradelineIds?: string[];
  selectedTradelines?: ParsedTradeline[];
}

interface UserInfo {
  name: string;
  address: string;
  city: string;
  state: string;
  zip: string;
}

const DisputeLetterPage = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [tradelines, setTradelines] = useState<ParsedTradeline[]>([]);
  const [selectedTradelines, setSelectedTradelines] = useState<ParsedTradeline[]>([]);
  const [userInfo, setUserInfo] = useState<UserInfo>({ 
    name: "",
    address: "", 
    city: "", 
    state: "", 
    zip: ""
  });
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
      console.log("=== DEBUG: Starting loadData ===");
      console.log("User ID:", user?.id);
      console.log("Location state:", location.state);

      try {
        const state = location.state as LocationState;
        
        // If tradelines were passed directly from the previous page
        if (state?.selectedTradelines && state.selectedTradelines.length > 0) {
          console.log("=== Using tradelines from navigation state ===", state.selectedTradelines);
          setTradelines(state.selectedTradelines);
          setSelectedTradelines(state.selectedTradelines);
        } else {
          // Fetch tradelines from database
          const userTradelines = await fetchUserTradelines(user.id);
          console.log("=== Fetched tradelines from DB ===", userTradelines);
          setTradelines(userTradelines);

          // Get selected tradeline IDs from navigation state
          const selectedIds = state?.selectedTradelineIds || [];
          console.log("=== Selected IDs from navigation ===", selectedIds);
          
          if (selectedIds.length > 0) {
            const preSelected = userTradelines.filter(tl => 
              selectedIds.includes(tl.id || '')
            );
            console.log("=== Pre-selected tradelines ===", preSelected);
            setSelectedTradelines(preSelected);
          }
        }

        // Autofill user info from profile
        setUserInfo({
          name: user.email || "",
          address: "",
          city: "",
          state: "",
          zip: ""
        });

      } catch (error) {
        console.error("=== Error in loadData ===", error);
        toast({ title: "Error", description: "Failed to load tradelines or user info." });
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [user, navigate, location.state]);

  const handleProceed = () => {
    console.log("Proceed to Step 3 button clicked.");
    console.log("Selected Tradelines:", selectedTradelines);
    navigate("/dispute-packet", {
      state: {
        selectedTradelines: selectedTradelines,
        userInfo: userInfo,
        letter: letter
      }
    });
  };

  // Only allow selection of negative tradelines
  const negativeTradelines = tradelines.filter((t) => t.is_negative);

  return (
    <MainLayout>
      <div className="min-h-screen bg-background text-foreground py-10 px-4 md:px-10">
        <Card className="max-w-6xl mx-auto space-y-6">
          <CardHeader>
            <CardTitle className="text-2xl">Step 2: Draft Dispute Letter</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {loading ? (
              <div className="flex items-center justify-center p-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                <p className="ml-2">Loading tradelines...</p>
              </div>
            ) : (
              <>
                <TradelineList
                  tradelines={negativeTradelines}
                  selected={selectedTradelines}
                  setSelected={setSelectedTradelines}
                  onAddManual={() => toast({ title: "Info", description: "Manual add not available here." })}
                />

                <UserInfoForm userInfo={userInfo} onChange={setUserInfo} />

                <LetterEditor
                  selectedTradelines={selectedTradelines}
                  letter={letter}
                  setLetter={setLetter}
                />

                <div className="flex justify-end space-x-4">
                  <Button 
                    variant="outline" 
                    onClick={() => navigate("/credit-report-upload")}
                  >
                    Back to Step 1
                  </Button>
                  <Button onClick={handleProceed} disabled={selectedTradelines.length === 0}>
                    Proceed to Step 3 ({selectedTradelines.length} selected)
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
