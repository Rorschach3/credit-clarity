"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useNavigate } from "react-router-dom";

const DisputeConfirmationPage = () => {
  const navigate = useNavigate();

  return (
    <main className="min-h-screen bg-background text-foreground py-10 px-4 md:px-10">
      <Card className="max-w-2xl mx-auto text-center space-y-6">
        <CardHeader>
          <CardTitle className="text-2xl">🎉 Dispute Submitted</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-lg">
            Your dispute packet has been submitted successfully.
          </p>
          <p className="text-sm text-muted-foreground">
            Please allow 30–45 days for the credit bureaus to respond.
            You can track the progress in your dispute history.
          </p>
          <div className="flex justify-center gap-4 mt-6">
            <Button variant="secondary" onClick={() => navigate("/dashboard")}>
              Return to Dashboard
            </Button>
            <Button onClick={() => navigate("/dispute-history")}>
              View Dispute History
            </Button>
          </div>
        </CardContent>
      </Card>
    </main>
  );
};

export default DisputeConfirmationPage;
