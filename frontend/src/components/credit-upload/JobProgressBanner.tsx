import React from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Copy, XCircle, CircleCheck, Loader2, Terminal } from 'lucide-react';
import { type JobStatus } from '@/services/jobPollingService';

interface JobProgressBannerProps {
  jobId: string;
  status: JobStatus | null;
  onCancel: (jobId: string) => void;
  onHide?: () => void;
}

export const JobProgressBanner: React.FC<JobProgressBannerProps> = ({ jobId, status, onCancel, onHide }) => {
  const percent = status?.progress ?? 0;
  const isCompleted = status?.status === 'completed';
  const isFailed = status?.status === 'failed' || status?.status === 'cancelled';
  const isRunning = status?.status === 'running' || status?.status === 'pending';
  const message = status?.message || (isCompleted ? 'Completed' : isFailed ? 'Failed' : 'Processing...');

  const curlCmd = `curl -s http://localhost:8000/api/job/${jobId}`;

  const copyCurl = async () => {
    try {
      await navigator.clipboard.writeText(curlCmd);
    } catch {}
  };

  return (
    <Card className={
      isCompleted ? 'border-green-200 bg-green-50 dark:bg-green-900/20' :
      isFailed ? 'border-red-200 bg-red-50 dark:bg-red-900/20' :
      'border-blue-200 bg-blue-50 dark:bg-blue-900/20'
    }>
      <CardContent className="py-4">
        <div className="flex flex-col md:flex-row md:items-center gap-3">
          <div className="flex items-center gap-2 min-w-0">
            {isCompleted ? (
              <CircleCheck className="h-5 w-5 text-green-600" />
            ) : isFailed ? (
              <XCircle className="h-5 w-5 text-red-600" />
            ) : (
              <Loader2 className="h-5 w-5 animate-spin" />
            )}
            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <span className="font-medium truncate">Background processing</span>
                <Badge variant="secondary">{status?.status ?? 'queued'}</Badge>
                <Badge variant="secondary">{percent}%</Badge>
              </div>
              <p className="text-sm text-muted-foreground truncate" title={message}>{message}</p>
              <p className="text-xs text-muted-foreground truncate">Job ID: {jobId}</p>
            </div>
          </div>

          <div className="flex-1">
            <Progress value={percent} />
          </div>

          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={copyCurl} title="Copy curl command">
              <Terminal className="h-4 w-4 mr-1" /> Copy curl
            </Button>
            {isRunning && (
              <Button variant="destructive" size="sm" onClick={() => onCancel(jobId)}>
                Cancel
              </Button>
            )}
            {onHide && (
              <Button variant="ghost" size="sm" onClick={onHide}>Hide</Button>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default JobProgressBanner;
