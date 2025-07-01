
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/hooks/use-auth";

interface SubscriptionPromptProps {
  onSubscribe: () => void;
  featureName?: string;
}

export function SubscriptionPrompt({ 
  onSubscribe 
}: SubscriptionPromptProps) {
  const { user } = useAuth();
  const navigate = useNavigate();

  // For free features, we can just proceed without a subscription check
  setTimeout(onSubscribe, 0);
  return null;
}
