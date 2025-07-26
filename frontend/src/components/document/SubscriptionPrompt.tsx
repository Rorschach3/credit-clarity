
interface SubscriptionPromptProps {
  onSubscribe: () => void;
  featureName?: string;
}

export function SubscriptionPrompt({ 
  onSubscribe 
}: SubscriptionPromptProps) {
  // For free features, we can just proceed without a subscription check
  setTimeout(onSubscribe, 0);
  return null;
}
