
import { ReactNode } from 'react';

interface StepIndicatorProps {
  currentStep: string;
  steps: {
    id: string;
    title: string;
    description: string;
    icon: ReactNode;
  }[];
}

export function StepIndicator({ currentStep, steps }: StepIndicatorProps) {
  // Helper function to get the step icon
  const getStepIcon = (step: string, thisStep: string, icon: ReactNode) => {
    if (step === thisStep) {
      return <div className="w-10 h-10 rounded-full bg-primary flex items-center justify-center text-white font-bold">{icon}</div>;
    }
    return <div className="w-10 h-10 rounded-full bg-muted flex items-center justify-center text-muted-foreground">{icon}</div>;
  };

  return (
    <div className="flex items-center justify-center mb-10 overflow-x-auto">
      <div className="flex items-center min-w-max">
        {steps.map((step, index) => (
          <div key={step.id} className="flex items-center min-w-max">
            {getStepIcon(currentStep, step.id, step.icon)}
            <div className="ml-2 mr-6">
              <p className={`font-medium ${currentStep === step.id ? 'text-primary' : ''}`}>{step.title}</p>
              <p className="text-xs text-muted-foreground">{step.description}</p>
            </div>
            {index < steps.length - 1 && <div className="w-16 h-[2px] bg-muted"></div>}
          </div>
        ))}
      </div>
    </div>
  );
}
