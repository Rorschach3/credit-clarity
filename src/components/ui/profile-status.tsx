import React from 'react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Loader2, User, AlertCircle, CheckCircle, RefreshCw } from 'lucide-react';

interface ProfileStatusProps {
  loading: boolean;
  error: string | null;
  isComplete: boolean;
  missingFields: string[];
  onRefresh: () => void;
  onEdit: () => void;
  className?: string;
}

export const ProfileStatus: React.FC<ProfileStatusProps> = ({
  loading,
  error,
  isComplete,
  missingFields,
  onRefresh,
  onEdit,
  className = ""
}) => {
  const getStatusIcon = () => {
    if (loading) return <Loader2 className="h-4 w-4 animate-spin" />;
    if (error) return <AlertCircle className="h-4 w-4 text-red-500" />;
    if (isComplete) return <CheckCircle className="h-4 w-4 text-green-500" />;
    return <User className="h-4 w-4 text-yellow-500" />;
  };

  const getStatusText = () => {
    if (loading) return "Loading profile...";
    if (error) return `Error: ${error}`;
    if (isComplete) return "Profile complete";
    return `Missing: ${missingFields.join(', ')}`;
  };

  const getStatusVariant = () => {
    if (loading) return "secondary";
    if (error) return "destructive";
    if (isComplete) return "default";
    return "outline";
  };

  return (
    <Card className={`${className} border-dashed`}>
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {getStatusIcon()}
            <span className="text-sm font-medium">Profile Status</span>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant={getStatusVariant()}>
              {getStatusText()}
            </Badge>
            <Button
              variant="ghost"
              size="sm"
              onClick={onRefresh}
              disabled={loading}
              className="h-8 w-8 p-0"
            >
              <RefreshCw className="h-3 w-3" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={onEdit}
              disabled={loading}
              className="h-8 px-2"
            >
              Edit
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};