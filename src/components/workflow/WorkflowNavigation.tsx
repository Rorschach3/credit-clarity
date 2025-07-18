import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { 
  Upload, 
  FileText, 
  Package, 
  ChevronLeft, 
  ChevronRight, 
  CheckCircle,
  Circle,
  ArrowRight
} from 'lucide-react';

interface WorkflowStep {
  id: string;
  title: string;
  description: string;
  path: string;
  icon: React.ReactNode;
  isCompleted: boolean;
  isActive: boolean;
  canAccess: boolean;
}

interface WorkflowNavigationProps {
  currentStep: 'upload' | 'tradelines' | 'dispute';
  onNext?: () => void;
  onPrevious?: () => void;
  canProceed?: boolean;
  nextLabel?: string;
  previousLabel?: string;
  completionData?: {
    hasUploadedReports: boolean;
    hasSelectedTradelines: boolean;
    hasGeneratedLetter: boolean;
  };
}

export const WorkflowNavigation: React.FC<WorkflowNavigationProps> = ({
  currentStep,
  onNext,
  onPrevious,
  canProceed = true,
  nextLabel,
  previousLabel,
  completionData = {
    hasUploadedReports: false,
    hasSelectedTradelines: false,
    hasGeneratedLetter: false
  }
}) => {
  const navigate = useNavigate();
  const location = useLocation();

  const steps: WorkflowStep[] = [
    {
      id: 'upload',
      title: 'Upload Reports',
      description: 'Upload credit reports to extract tradelines',
      path: '/credit-report-upload',
      icon: <Upload className="h-5 w-5" />,
      isCompleted: completionData.hasUploadedReports,
      isActive: currentStep === 'upload',
      canAccess: true
    },
    {
      id: 'tradelines',
      title: 'Select Tradelines',
      description: 'Choose negative items to dispute',
      path: '/tradelines',
      icon: <FileText className="h-5 w-5" />,
      isCompleted: completionData.hasSelectedTradelines,
      isActive: currentStep === 'tradelines',
      canAccess: completionData.hasUploadedReports || currentStep === 'tradelines'
    },
    {
      id: 'dispute',
      title: 'Generate Packet',
      description: 'Create and customize dispute letters',
      path: '/dispute-wizard',
      icon: <Package className="h-5 w-5" />,
      isCompleted: completionData.hasGeneratedLetter,
      isActive: currentStep === 'dispute',
      canAccess: completionData.hasSelectedTradelines || currentStep === 'dispute'
    }
  ];

  const currentStepIndex = steps.findIndex(step => step.id === currentStep);
  const nextStep = steps[currentStepIndex + 1];
  const previousStep = steps[currentStepIndex - 1];

  const handleStepClick = (step: WorkflowStep) => {
    if (step.canAccess) {
      navigate(step.path);
    }
  };

  const handleNext = () => {
    if (onNext) {
      onNext();
    } else if (nextStep) {
      navigate(nextStep.path);
    }
  };

  const handlePrevious = () => {
    if (onPrevious) {
      onPrevious();
    } else if (previousStep) {
      navigate(previousStep.path);
    }
  };

  return (
    <Card className="mb-6 border-primary/20 bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-950/20 dark:to-purple-950/20">
      <CardContent className="p-6">
        
        {/* Progress Steps */}
        <div className="mb-6">
          <div className="flex items-center justify-between relative">
            {/* Progress Line */}
            <div className="absolute top-5 left-0 right-0 h-0.5 bg-gray-200 dark:bg-gray-700" />
            <div 
              className="absolute top-5 left-0 h-0.5 bg-primary transition-all duration-500"
              style={{ 
                width: `${(currentStepIndex / (steps.length - 1)) * 100}%` 
              }}
            />
            
            {steps.map((step, index) => (
              <div key={step.id} className="relative z-10 flex flex-col items-center">
                <button
                  onClick={() => handleStepClick(step)}
                  disabled={!step.canAccess}
                  className={`
                    w-10 h-10 rounded-full border-2 flex items-center justify-center transition-all duration-200
                    ${step.isActive 
                      ? 'border-primary bg-primary text-primary-foreground shadow-lg' 
                      : step.isCompleted
                        ? 'border-green-500 bg-green-500 text-white'
                        : step.canAccess
                          ? 'border-gray-300 bg-white hover:border-primary hover:bg-primary hover:text-primary-foreground cursor-pointer'
                          : 'border-gray-200 bg-gray-100 text-gray-400 cursor-not-allowed'
                    }
                  `}
                >
                  {step.isCompleted ? (
                    <CheckCircle className="h-5 w-5" />
                  ) : step.isActive ? (
                    step.icon
                  ) : (
                    <Circle className="h-5 w-5" />
                  )}
                </button>
                
                <div className="mt-2 text-center">
                  <div className={`text-sm font-medium ${
                    step.isActive ? 'text-primary' : 
                    step.isCompleted ? 'text-green-600' : 
                    step.canAccess ? 'text-foreground' : 'text-muted-foreground'
                  }`}>
                    {step.title}
                  </div>
                  <div className="text-xs text-muted-foreground max-w-24 leading-tight">
                    {step.description}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Current Step Info */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-primary/10 rounded-lg">
              {steps[currentStepIndex].icon}
            </div>
            <div>
              <h3 className="font-semibold text-lg">
                Step {currentStepIndex + 1}: {steps[currentStepIndex].title}
              </h3>
              <p className="text-muted-foreground">
                {steps[currentStepIndex].description}
              </p>
            </div>
          </div>

          <Badge variant={steps[currentStepIndex].isCompleted ? "default" : "secondary"}>
            {steps[currentStepIndex].isCompleted ? 'Completed' : 'In Progress'}
          </Badge>
        </div>

        {/* Navigation Buttons */}
        <div className="flex items-center justify-between mt-6 pt-4 border-t">
          <div>
            {previousStep && (
              <Button
                variant="outline"
                onClick={handlePrevious}
                className="flex items-center gap-2"
              >
                <ChevronLeft className="h-4 w-4" />
                {previousLabel || `Back to ${previousStep.title}`}
              </Button>
            )}
          </div>

          <div className="flex items-center gap-3">
            {nextStep && (
              <Button
                onClick={handleNext}
                disabled={!canProceed}
                className="flex items-center gap-2"
              >
                {nextLabel || `Continue to ${nextStep.title}`}
                <ChevronRight className="h-4 w-4" />
              </Button>
            )}
            
            {!nextStep && currentStep === 'dispute' && (
              <Button className="flex items-center gap-2">
                <CheckCircle className="h-4 w-4" />
                Complete Process
              </Button>
            )}
          </div>
        </div>

        {/* Help Text */}
        <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-950/20 rounded-lg">
          <div className="flex items-start gap-2">
            <ArrowRight className="h-4 w-4 text-blue-600 mt-0.5" />
            <div className="text-sm text-blue-700 dark:text-blue-300">
              {currentStep === 'upload' && (
                "Upload your credit reports from all three bureaus (Experian, Equifax, TransUnion) to extract tradeline information automatically."
              )}
              {currentStep === 'tradelines' && (
                "Review and select the negative tradelines you want to dispute. You can select items from one bureau at a time to create targeted dispute packets."
              )}
              {currentStep === 'dispute' && (
                "Generate personalized dispute letters, add supporting documents, and download your complete dispute packet ready for mailing."
              )}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};