import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { AlertCircle } from 'lucide-react';

interface ProfileRequirementsProps {
  disputeProfile: any;
  isProfileComplete: boolean;
  missingFields: string[];
}

export const ProfileRequirements: React.FC<ProfileRequirementsProps> = ({
  disputeProfile,
  isProfileComplete,
  missingFields
}) => {
  const navigate = useNavigate();

  if (disputeProfile && isProfileComplete) {
    return null;
  }

  return (
    <Card className="border-yellow-200 bg-yellow-50">
      <CardContent className="p-4">
        <div className="flex items-center gap-2 text-yellow-800">
          <AlertCircle className="h-5 w-5" />
          <div>
            <div className="font-medium">
              {!disputeProfile ? 'Profile Required' : 'Profile Incomplete'}
            </div>
            <div className="text-sm">
              {!disputeProfile ? 
                'Complete your profile to generate personalized dispute letters.' :
                `Missing required fields: ${missingFields.join(', ')}`
              }{' '}
              <Button 
                variant="link" 
                className="p-0 h-auto text-yellow-800 underline"
                onClick={() => navigate('/profile')}
              >
                {!disputeProfile ? 'Complete Profile' : 'Update Profile'}
              </Button>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};