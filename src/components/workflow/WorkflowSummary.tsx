import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { 
  CheckCircle, 
  Upload, 
  FileText, 
  Package, 
  ArrowRight,
  Download,
  Mail
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';

interface WorkflowSummaryProps {
  completionData: {
    hasUploadedReports: boolean;
    hasSelectedTradelines: boolean;
    hasGeneratedLetter: boolean;
  };
  tradelinesCount?: number;
  selectedTradelinesCount?: number;
  generatedLettersCount?: number;
}

export const WorkflowSummary: React.FC<WorkflowSummaryProps> = ({
  completionData,
  tradelinesCount = 0,
  selectedTradelinesCount = 0,
  generatedLettersCount = 0
}) => {
  const navigate = useNavigate();

  const steps = [
    {
      id: 'upload',
      title: 'Reports Uploaded',
      icon: <Upload className="h-5 w-5" />,
      isCompleted: completionData.hasUploadedReports,
      description: completionData.hasUploadedReports 
        ? `${tradelinesCount} tradelines extracted`
        : 'Upload credit reports',
      path: '/credit-report-upload'
    },
    {
      id: 'tradelines',
      title: 'Tradelines Selected',
      icon: <FileText className="h-5 w-5" />,
      isCompleted: completionData.hasSelectedTradelines,
      description: completionData.hasSelectedTradelines
        ? `${selectedTradelinesCount} items selected`
        : 'Select negative items',
      path: '/tradelines'
    },
    {
      id: 'dispute',
      title: 'Packet Generated',
      icon: <Package className="h-5 w-5" />,
      isCompleted: completionData.hasGeneratedLetter,
      description: completionData.hasGeneratedLetter
        ? `${generatedLettersCount} letters created`
        : 'Generate dispute packet',
      path: '/dispute-wizard'
    }
  ];

  const completedSteps = steps.filter(step => step.isCompleted).length;
  const totalSteps = steps.length;
  const progressPercentage = (completedSteps / totalSteps) * 100;

  const nextStep = steps.find(step => !step.isCompleted);

  return (
    <Card className="border-primary/20">
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>Dispute Process Progress</span>
          <Badge variant={completedSteps === totalSteps ? "default" : "secondary"}>
            {completedSteps}/{totalSteps} Complete
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        
        {/* Progress Bar */}
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span>Overall Progress</span>
            <span>{Math.round(progressPercentage)}%</span>
          </div>
          <Progress value={progressPercentage} className="h-2" />
        </div>

        {/* Steps List */}
        <div className="space-y-3">
          {steps.map((step, index) => (
            <div 
              key={step.id}
              className={`flex items-center gap-3 p-3 rounded-lg border transition-colors ${
                step.isCompleted 
                  ? 'bg-green-50 border-green-200 dark:bg-green-950/20 dark:border-green-800'
                  : 'bg-gray-50 border-gray-200 dark:bg-gray-900/20 dark:border-gray-700'
              }`}
            >
              <div className={`p-2 rounded-full ${
                step.isCompleted 
                  ? 'bg-green-500 text-white'
                  : 'bg-gray-300 text-gray-600'
              }`}>
                {step.isCompleted ? <CheckCircle className="h-4 w-4" /> : step.icon}
              </div>
              
              <div className="flex-1">
                <div className="font-medium">{step.title}</div>
                <div className="text-sm text-muted-foreground">{step.description}</div>
              </div>

              {!step.isCompleted && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => navigate(step.path)}
                  className="flex items-center gap-1"
                >
                  Go to Step
                  <ArrowRight className="h-3 w-3" />
                </Button>
              )}
            </div>
          ))}
        </div>

        {/* Next Action */}
        <div className="pt-4 border-t">
          {completedSteps === totalSteps ? (
            <div className="text-center space-y-3">
              <div className="flex items-center justify-center gap-2 text-green-600 dark:text-green-400">
                <CheckCircle className="h-5 w-5" />
                <span className="font-medium">Process Complete!</span>
              </div>
              <p className="text-sm text-muted-foreground">
                Your dispute packet is ready. Print, sign, and mail with certified mail.
              </p>
              <div className="flex gap-2 justify-center">
                <Button variant="outline" size="sm">
                  <Download className="h-4 w-4 mr-1" />
                  Download Packet
                </Button>
                <Button variant="outline" size="sm">
                  <Mail className="h-4 w-4 mr-1" />
                  Mailing Guide
                </Button>
              </div>
            </div>
          ) : nextStep ? (
            <div className="text-center space-y-3">
              <p className="text-sm text-muted-foreground">
                Next: {nextStep.description}
              </p>
              <Button 
                onClick={() => navigate(nextStep.path)}
                className="flex items-center gap-2"
              >
                Continue to {nextStep.title}
                <ArrowRight className="h-4 w-4" />
              </Button>
            </div>
          ) : null}
        </div>
      </CardContent>
    </Card>
  );
};