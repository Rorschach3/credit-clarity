import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { User } from 'lucide-react';

interface ProfileSummaryProps {
  disputeProfile: any;
  isProfileComplete: boolean;
}

export const ProfileSummary: React.FC<ProfileSummaryProps> = ({
  disputeProfile,
  isProfileComplete
}) => {
  if (!disputeProfile) {
    return null;
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg flex items-center gap-2">
          <User className="h-5 w-5" />
          Profile Information
          <Badge variant={isProfileComplete ? "default" : "secondary"} className="ml-auto">
            {isProfileComplete ? 'Complete' : 'Incomplete'}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          <div>
            <span className="font-medium">Name:</span> {disputeProfile.firstName} {disputeProfile.lastName}
          </div>
          <div>
            <span className="font-medium">Address:</span> {disputeProfile.address}
          </div>
          <div>
            <span className="font-medium">City:</span> {disputeProfile.city}
          </div>
          <div>
            <span className="font-medium">State:</span> {disputeProfile.state}
          </div>
          <div>
            <span className="font-medium">ZIP:</span> {disputeProfile.zipCode}
          </div>
          <div>
            <span className="font-medium">SSN:</span> {disputeProfile.ssn ? `***-**-${disputeProfile.ssn.slice(-4)}` : 'Not provided'}
          </div>
          <div>
            <span className="font-medium">Date of Birth:</span> {disputeProfile.dateOfBirth || 'Not provided'}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};