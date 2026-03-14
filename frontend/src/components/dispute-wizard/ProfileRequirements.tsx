import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { AlertCircle } from 'lucide-react';

interface ProfileRequirementsProps {
  disputeProfile: any;
  isProfileComplete: boolean;
  missingFields: string[];
}

const FIELD_LABELS: Record<string, string> = {
  first_name:       'First name',
  last_name:        'Last name',
  address1:         'Street address',
  city:             'City',
  state:            'State',
  zip_code:         'Zip code',
  last_four_of_ssn: 'SSN last 4 digits',
};

const humanize = (fields: string[]) =>
  fields.map((f) => FIELD_LABELS[f] ?? f).join(', ');

export const ProfileRequirements: React.FC<ProfileRequirementsProps> = ({
  disputeProfile,
  isProfileComplete,
  missingFields,
}) => {
  const navigate = useNavigate();

  if (disputeProfile && isProfileComplete) return null;

  return (
    <div className="flex items-start gap-3 rounded-lg border border-amber-500/30 bg-amber-500/10 p-4">
      <AlertCircle className="h-5 w-5 text-amber-400 mt-0.5 flex-shrink-0" />
      <div className="text-sm">
        <p className="font-semibold text-amber-300 mb-1">
          {!disputeProfile ? 'Profile required' : 'Profile incomplete'}
        </p>
        <p className="text-amber-200/80 mb-2">
          {!disputeProfile
            ? 'Complete your profile to generate personalized dispute letters.'
            : `Missing: ${humanize(missingFields)}.`}
        </p>
        <Button
          size="sm"
          className="btn-gold rounded-md h-8 px-4 text-xs"
          onClick={() => navigate('/profile')}
        >
          {!disputeProfile ? 'Complete Profile' : 'Update Profile'}
        </Button>
      </div>
    </div>
  );
};
