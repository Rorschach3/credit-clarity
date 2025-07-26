"use client";

import React, { useState, useEffect, useRef, ChangeEvent } from "react";
import { createWorker, Worker } from "tesseract.js";
import { useNavigate } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { toast } from "@/components/ui/use-toast";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { pdfToImages } from "@/utils/pdfToImage";
import { useAuth } from "@/hooks/use-auth";
import MainLayout from "@/components/layout/MainLayout";
import {
  ParsedTradeline,
  ParsedTradelineSchema,
  saveTradelinesToDatabase,
  parseTradelinesFromText,
  fetchUserTradelines,
} from "@/utils/tradelineParser";
import { z } from "zod";
import { supabase } from "../../supabase/client";
import { ManualTradelineModal } from "@/components/disputes/ManualTradelineModal";
import { UserInfoForm } from "@/components/disputes/UserInfoForm";
import { LetterEditor } from "@/components/disputes/LetterEditor";
import { TradelineList } from "@/components/disputes/TradelineList";
import { DocumentUploadSection } from "@/components/disputes/DocumentUploadSection";
import { MailingInstructions } from "@/components/disputes/MailingInstructions";

const DisputesPage = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [tradelines, setTradelines] = useState<z.infer<typeof ParsedTradelineSchema>[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [manualModalOpen, setManualModalOpen] = useState(false);
  const workerRef = useRef<Worker | null>(null);

  const [selectedTradelines, setSelectedTradelines] = useState<ParsedTradeline[]>([]);
  const [userInfo, setUserInfo] = useState({ name: "", address: "", city: "", state: "", zip: "" });
  const [letter, setLetter] = useState("");
  const [loading, setLoading] = useState(true);

  const [showDocsSection, setShowDocsSection] = useState(false);
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    (async () => {
      workerRef.current = await createWorker();
    })();
    return () => {
      workerRef.current?.terminate();
    };
  }, []);

  const handleFileUpload = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file || file.type !== "application/pdf") {
      toast({ title: "Invalid file", description: "Please upload a PDF file." });
      return;
    }

    setIsUploading(true);
    setUploadProgress(0);
    setTradelines([]);

    try {
      const buffer = await file.arrayBuffer();
      const images = await pdfToImages(buffer);
      let textContent = "";
      for (let i = 0; i < images.length; i++) {
        if (!workerRef.current) throw new Error("Worker not initialized");
        const { data } = await workerRef.current.recognize(images[i]);
        textContent += data.text + "\n";
        setUploadProgress(((i + 1) / images.length) * 100);
      }
      const parsed = parseTradelinesFromText(textContent);
      setTradelines(parsed);
      if (user) {
        try {
          await saveTradelinesToDatabase(parsed, user.id);
          toast({ title: "Upload complete", description: "Tradelines extracted and saved." });
        } catch (dbError) {
          console.error("Database error:", dbError);
          toast({ title: "Database Error", description: "Failed to save tradelines to the database." });
        }
      }
    } catch (error) {
      console.error("File processing error:", error);
      toast({ title: "File Error", description: "Failed to process PDF." });
    } finally {
      setIsUploading(false);
    }
  };

  const updateTradeline = (index: number, updated: Partial<ParsedTradeline>) => {
    setTradelines((prev) => {
      const newTradelines = [...prev];
      newTradelines[index] = { ...newTradelines[index], ...updated };
      return newTradelines;
    });
  };

  const deleteTradeline = (index: number) => {
    setTradelines((prev) => prev.filter((_, i) => i !== index));
  };

  useEffect(() => {
    if (!user) {
      toast({ title: "Error", description: "User not authenticated." });
      navigate("/login");
      return;
    }

    const loadData = async () => {
      setLoading(true);
      try {
        const userTradelines = await fetchUserTradelines(user.id);
        setTradelines(userTradelines);
        setUserInfo({ name: user.email || "", address: "", city: "", state: "", zip: "" });
      } catch (error) {
        toast({ title: "Error", description: "Failed to load tradelines or user info." });
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [user, navigate]);

  const negativeTradelines = tradelines.filter((t) => t.isNegative);

  const handleGeneratePacket = async () => {
    setGenerating(true);
    try {
      toast({ title: "Packet Generated", description: "Dispute packet generated successfully!" });
    } catch (error) {
      console.error("Error generating packet:", error);
      toast({ title: "Generation Failed", description: "There was a problem generating your packet. Please try again.", variant: "destructive" });
    } finally {
      setGenerating(false);
    }
  };

  return (
    <MainLayout>
      <div className="min-h-screen bg-background text-foreground py-10 px-4 md:px-10">
        <Card className="max-w-6xl mx-auto space-y-6">
          <CardHeader>
            <CardTitle className="text-2xl">Dispute Center</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Tabs logic continues here... */}
          </CardContent>
        </Card>
      </div>
    </MainLayout>
  );
};

export default DisputesPage;
