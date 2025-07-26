import React from 'react';
import { Card, CardContent } from './card';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({ 
  size = 'md', 
  className = '' 
}) => {
  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-8 w-8', 
    lg: 'h-12 w-12'
  };

  return (
    <div className={`animate-spin rounded-full border-b-2 border-primary ${sizeClasses[size]} ${className}`} />
  );
};

interface PageLoadingProps {
  message?: string;
}

export const PageLoading: React.FC<PageLoadingProps> = ({ 
  message = 'Loading...' 
}) => {
  return (
    <div className="min-h-screen bg-background text-foreground flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardContent className="flex flex-col items-center justify-center py-8">
          <LoadingSpinner size="lg" className="mb-4" />
          <p className="text-muted-foreground text-center">{message}</p>
        </CardContent>
      </Card>
    </div>
  );
};

interface ComponentLoadingProps {
  message?: string;
  className?: string;
}

export const ComponentLoading: React.FC<ComponentLoadingProps> = ({ 
  message = 'Loading...', 
  className = '' 
}) => {
  return (
    <div className={`flex items-center justify-center p-8 ${className}`}>
      <div className="text-center">
        <LoadingSpinner className="mx-auto mb-4" />
        <p className="text-muted-foreground">{message}</p>
      </div>
    </div>
  );
};

// Specialized loading components for specific routes
export const DisputeWizardLoading: React.FC = () => (
  <PageLoading message="Loading Dispute Wizard..." />
);

export const CreditReportUploadLoading: React.FC = () => (
  <PageLoading message="Preparing Credit Report Upload..." />
);

export const TradelinesLoading: React.FC = () => (
  <PageLoading message="Loading Tradelines..." />
);

export const ProfileLoading: React.FC = () => (
  <PageLoading message="Loading Profile..." />
);

export const DashboardLoading: React.FC = () => (
  <PageLoading message="Loading Dashboard..." />
);