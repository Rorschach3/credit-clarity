import React, { useEffect, useState, useCallback } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { jobPollingService, type JobStatus } from '@/services/jobPollingService';
import { RefreshCcw, PlayCircle, ExternalLink } from 'lucide-react';

interface RecentJobsPanelProps {
  userId: string;
  onResume: (jobId: string) => void;
}

export const RecentJobsPanel: React.FC<RecentJobsPanelProps> = ({ userId, onResume }) => {
  const [jobs, setJobs] = useState<Array<{
    job_id: string;
    status: string;
    progress: number;
    message: string;
    created_at: string;
    task_name: string;
  }>>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadJobs = useCallback(async () => {
    if (!userId) return;
    setLoading(true);
    setError(null);
    const res = await jobPollingService.getUserJobs(userId, 10);
    if (res.success) {
      setJobs(res.jobs || []);
    } else {
      setError(res.error || 'Failed to load jobs');
    }
    setLoading(false);
  }, [userId]);

  useEffect(() => {
    loadJobs();
    const id = setInterval(loadJobs, 30000); // refresh every 30s
    return () => clearInterval(id);
  }, [loadJobs]);

  const statusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'failed':
      case 'cancelled':
        return 'bg-red-100 text-red-800';
      case 'running':
        return 'bg-blue-100 text-blue-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between py-3">
        <CardTitle className="text-base">Recent Jobs</CardTitle>
        <Button variant="outline" size="sm" onClick={loadJobs} disabled={loading}>
          <RefreshCcw className="h-4 w-4 mr-1" /> Refresh
        </Button>
      </CardHeader>
      <CardContent>
        {error && <p className="text-sm text-red-600 mb-2">{error}</p>}
        {jobs.length === 0 ? (
          <p className="text-sm text-muted-foreground">No recent jobs found.</p>
        ) : (
          <div className="space-y-2">
            {jobs.map((job) => (
              <div key={job.job_id} className="flex items-center gap-3 p-2 rounded-md border">
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <Badge className={statusColor(job.status)} variant="secondary">{job.status}</Badge>
                    <span className="text-sm font-medium truncate">{job.task_name || 'credit-report'}</span>
                    <span className="text-xs text-muted-foreground">{new Date(job.created_at).toLocaleString()}</span>
                  </div>
                  <p className="text-xs text-muted-foreground truncate" title={job.message}>{job.message}</p>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant="secondary">{job.progress}%</Badge>
                  {(job.status === 'pending' || job.status === 'running') && (
                    <Button size="sm" onClick={() => onResume(job.job_id)}>
                      <PlayCircle className="h-4 w-4 mr-1" /> Resume
                    </Button>
                  )}
                  <Button variant="outline" size="sm" onClick={() => window.open(`http://localhost:8000/api/job/${job.job_id}`, '_blank')}>
                    <ExternalLink className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default RecentJobsPanel;
