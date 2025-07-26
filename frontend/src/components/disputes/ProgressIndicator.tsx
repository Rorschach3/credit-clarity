
import { Progress } from "@/components/ui/progress";

interface ProgressIndicatorProps {
  currentStep: string;
  steps: string[];
}

export function ProgressIndicator({ currentStep, steps }: ProgressIndicatorProps) {
  // Calculate progress percentage
  const getProgressPercentage = () => {
    const currentIndex = steps.indexOf(currentStep);
    return ((currentIndex) / (steps.length - 1)) * 100;
  };
  
  return (
    <>
      <div className="mb-2 flex justify-between items-center">
        <span className="text-sm font-medium">Progress</span>
        <span className="text-sm text-muted-foreground">{Math.round(getProgressPercentage())}%</span>
      </div>
      <Progress value={getProgressPercentage()} className="mb-8" />
    </>
  );
}
