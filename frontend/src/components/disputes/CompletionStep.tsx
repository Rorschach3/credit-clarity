
import { Button } from "@/components/ui/button";

interface CompletionStepProps {
  onRestart: () => void;
}

export function CompletionStep({ onRestart }: CompletionStepProps) {
  return (
    <div className="text-center py-12 space-y-6">
      <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-green-100 text-green-600">
        <CheckCircleIcon className="h-10 w-10" />
      </div>
      <h2 className="text-2xl font-bold">AI-Powered Dispute Process Complete!</h2>
      <p className="text-muted-foreground max-w-lg mx-auto">
        Your AI-optimized dispute letters have been created and saved. You can access them from your dashboard
        to print, download, or mail them directly to the credit bureaus.
      </p>
      <div className="pt-4">
        <Button onClick={onRestart}>
          Start New Dispute
        </Button>
      </div>
    </div>
  );
}

const CheckCircleIcon = (props: React.SVGProps<SVGSVGElement>) => (
  <svg
    {...props}
    xmlns="http://www.w3.org/2000/svg"
    width="24"
    height="24"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
    <polyline points="22 4 12 14.01 9 11.01"></polyline>
  </svg>
);
