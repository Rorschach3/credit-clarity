import React from 'react';
import { CardHeader, CardTitle } from '@/components/ui/card';
import { Package } from 'lucide-react';

export const DisputeWizardHeader: React.FC = () => {
  return (
    <CardHeader>
      <CardTitle className="text-2xl flex items-center gap-2">
        <Package className="h-6 w-6" />
        Generate Dispute Packet
      </CardTitle>
      <p className="text-muted-foreground">
        Create personalized dispute letters for negative tradelines using your profile information
      </p>
    </CardHeader>
  );
};