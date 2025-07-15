import React from 'react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Loader2, Database, AlertCircle, CheckCircle, RefreshCw } from 'lucide-react';

interface TradelinesStatusProps {
  loading: boolean;
  error: string | null;
  tradelinesCount: number;
  onRefresh: () => void;
  className?: string;
}

export const TradelinesStatus: React.FC<TradelinesStatusProps> = ({
  loading,
  error,
  tradelinesCount,
  onRefresh,
  className = ""
}) => {
  const getStatusIcon = () => {
    if (loading) return <Loader2 className="h-4 w-4 animate-spin" />;
    if (error) return <AlertCircle className="h-4 w-4 text-red-500" />;
    if (tradelinesCount > 0) return <CheckCircle className="h-4 w-4 text-green-500" />;
    return <Database className="h-4 w-4 text-gray-500" />;
  };

  const getStatusText = () => {
    if (loading) return "Loading tradelines...";
    if (error) return `Error: ${error}`;
    if (tradelinesCount > 0) return `${tradelinesCount} tradeline(s) loaded`;
    return "No tradelines found";
  };

  const getStatusVariant = () => {
    if (loading) return "secondary";
    if (error) return "destructive";
    if (tradelinesCount > 0) return "default";
    return "outline";
  };

  return (
    <Card className={`${className} border-dashed`}>
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {getStatusIcon()}
            <span className="text-sm font-medium">Database Status</span>
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
          </div>
        </div>
      </CardContent>
    </Card>
  );
};