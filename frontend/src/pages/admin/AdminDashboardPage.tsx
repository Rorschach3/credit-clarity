"use client";

import React from "react";
import { useAdminDisputes } from "@/hooks/admin/useAdminDisputes";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/spinner"; // or replace with a spinner you have

const AdminDashboardPage: React.FC = () => {
  const { disputes, loading, error } = useAdminDisputes();

  return (
    <main className="min-h-screen bg-background text-foreground py-10 px-4 md:px-10">
      <Card className="max-w-6xl mx-auto space-y-4">
        <CardHeader>
          <CardTitle className="text-2xl">Admin Dispute Dashboard</CardTitle>
        </CardHeader>

        <CardContent className="space-y-4">
          {loading && <Spinner />}
          {error && <p className="text-red-500">{error}</p>}

          {!loading && disputes.length === 0 && (
            <p className="text-muted-foreground">No disputes found.</p>
          )}

          {disputes.map((dispute) => (
            <div
              key={dispute.id}
              className="border p-4 rounded bg-muted hover:bg-accent transition"
            >
              <div className="flex justify-between items-center mb-2">
                <span className="font-medium">{dispute.email || dispute.user_id}</span>
                <Badge variant="outline">{dispute.status}</Badge>
              </div>
              <p className="text-sm text-muted-foreground">
                Created: {new Date(dispute.created_at).toLocaleDateString()}
              </p>
              <pre className="whitespace-pre-wrap text-xs mt-2 bg-background rounded p-2 border">
                {dispute.letter_content}
              </pre>
            </div>
          ))}
        </CardContent>
      </Card>
    </main>
  );
};

export default AdminDashboardPage;
