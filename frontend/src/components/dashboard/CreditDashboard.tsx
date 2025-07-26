import React, { useState, useMemo } from 'react';
import { 
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, 
  CartesianGrid, Tooltip, Legend, ResponsiveContainer 
} from 'recharts';
import { 
  CheckCircle, AlertCircle, Clock, 
  TrendingUp, FileText, Mail
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/hooks/use-auth";
import { usePersistentTradelines } from "@/hooks/usePersistentTradelines";
import { usePersistentProfile } from "@/hooks/usePersistentProfile";
import { useDashboardMetrics, useDashboardChartData } from "@/hooks/queries/useDashboardQueries";

const CreditDashboard: React.FC = () => {
  const { disputeProfile } = usePersistentProfile();
  const { 
    metrics: creditMetrics, 
    rawData, 
    isLoading: loading, 
    error,
    hasData,
    hasProfile,
    hasTradelines 
  } = useDashboardMetrics();
  
  const { chartData, isLoading: chartLoading } = useDashboardChartData();
  const [filter, setFilter] = useState({ bureau: "", priority: "", status: "" });
  
  // Extract disputes data for compatibility
  const disputeData = rawData?.disputes || [];

  // Filter disputes based on current filter
  const filteredDisputes = useMemo(() => {
    return disputeData.filter(dispute => {
      return (
        (filter.bureau === "" || dispute.bureau === filter.bureau) &&
        (filter.priority === "" || dispute.priority === filter.priority) &&
        (filter.status === "" || dispute.status === filter.status)
      );
    });
  }, [disputeData, filter]);

  // Bureau distribution data
  const bureauData = useMemo(() => {
    const distribution = disputeData.reduce((acc, dispute) => {
      acc[dispute.bureau] = (acc[dispute.bureau] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);
    
    return Object.entries(distribution).map(([bureau, count]) => ({
      bureau,
      count,
      percentage: Math.round((count / disputeData.length) * 100)
    }));
  }, [disputeData]);

  // Status distribution data
  const statusData = useMemo(() => {
    const statusCounts = disputeData.reduce((acc, dispute) => {
      acc[dispute.status] = (acc[dispute.status] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    return [
      { name: 'Completed', value: statusCounts.completed || 0, color: '#22c55e' },
      { name: 'In Progress', value: statusCounts.in_progress || 0, color: '#3b82f6' },
      { name: 'Pending', value: statusCounts.pending || 0, color: '#f59e0b' },
      { name: 'Rejected', value: statusCounts.rejected || 0, color: '#ef4444' }
    ];
  }, [disputeData]);

  // Recent activity timeline
  const timelineData = useMemo(() => {
    const last30Days = Array.from({ length: 30 }, (_, i) => {
      const date = new Date();
      date.setDate(date.getDate() - i);
      return date.toISOString().split('T')[0];
    }).reverse();

    return last30Days.map(date => {
      const disputes = disputeData.filter(d => d.dateCreated === date || d.dateUpdated === date);
      return {
        date: new Date(date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
        disputes: disputes.length,
        resolved: disputes.filter(d => d.status === 'completed').length
      };
    });
  }, [disputeData]);

  // Upcoming deadlines (mock data - would be based on dispute timelines)
  const upcomingDeadlines = useMemo(() => {
    return disputeData
      .filter(d => d.status === 'in_progress')
      .map(d => ({
        ...d,
        deadline: new Date(new Date(d.dateCreated).getTime() + 30 * 24 * 60 * 60 * 1000)
      }))
      .sort((a, b) => a.deadline.getTime() - b.deadline.getTime());
  }, [disputeData]);

  // Handle error state
  if (error) {
    return (
      <div className="min-h-screen bg-background text-foreground p-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <AlertCircle className="h-8 w-8 text-red-500 mx-auto mb-4" />
            <p className="text-muted-foreground">Error loading dashboard data</p>
            <Button onClick={refreshData} className="mt-4">
              Try Again
            </Button>
          </div>
        </div>
      </div>
    );
  }

  // Handle loading state
  if (loading) {
    return (
      <div className="min-h-screen bg-background text-foreground p-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
            <p className="text-muted-foreground">Loading dashboard data...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background text-foreground p-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Credit Repair Dashboard</h1>
        <p className="text-muted-foreground">
          {disputeProfile ? `Welcome back, ${disputeProfile.firstName}!` : 'Track your credit repair progress'}
        </p>
      </div>

      {/* Filter Controls */}
      <Card className="mb-8">
        <CardContent className="p-4">
          <div className="flex flex-wrap gap-4">
            <select 
              className="px-4 py-2 border rounded-md bg-background"
              value={filter.bureau}
              onChange={(e) => setFilter({...filter, bureau: e.target.value})}
            >
              <option value="">All Bureaus</option>
              <option value="Experian">Experian</option>
              <option value="TransUnion">TransUnion</option>
              <option value="Equifax">Equifax</option>
            </select>
            
            <select 
              className="px-4 py-2 border rounded-md bg-background"
              value={filter.priority}
              onChange={(e) => setFilter({...filter, priority: e.target.value})}
            >
              <option value="">All Priorities</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
            
            <select 
              className="px-4 py-2 border rounded-md bg-background"
              value={filter.status}
              onChange={(e) => setFilter({...filter, status: e.target.value})}
            >
              <option value="">All Status</option>
              <option value="completed">Completed</option>
              <option value="in_progress">In Progress</option>
              <option value="pending">Pending</option>
              <option value="rejected">Rejected</option>
            </select>
          </div>
        </CardContent>
      </Card>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Negative Items</CardTitle>
            <AlertCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{creditMetrics.totalNegativeItems}</div>
            <p className="text-xs text-muted-foreground">Total items to dispute</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Items Disputed</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{creditMetrics.itemsDisputed}</div>
            <p className="text-xs text-muted-foreground">Currently in process</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Items Resolved</CardTitle>
            <CheckCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{creditMetrics.itemsResolved}</div>
            <p className="text-xs text-muted-foreground">Successfully removed</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Potential Score Increase</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">+{creditMetrics.potentialScoreIncrease}</div>
            <p className="text-xs text-muted-foreground">Estimated points</p>
          </CardContent>
        </Card>
      </div>

      {/* Progress Overview */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle>Dispute Progress</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span>Overall Progress</span>
              <span className="font-semibold">
                {creditMetrics.itemsResolved}/{creditMetrics.itemsDisputed} resolved
              </span>
            </div>
            <Progress 
              value={creditMetrics.itemsDisputed > 0 ? (creditMetrics.itemsResolved / creditMetrics.itemsDisputed) * 100 : 0} 
              className="w-full"
            />
          </div>
        </CardContent>
      </Card>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
        <Card>
          <CardHeader>
            <CardTitle>Dispute Timeline</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={timelineData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="disputes" stroke="#3b82f6" name="New Disputes" />
                <Line type="monotone" dataKey="resolved" stroke="#22c55e" name="Resolved" />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Status Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={statusData}
                  cx="50%"
                  cy="50%"
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                  label={({ name, value }) => `${name}: ${value}`}
                >
                  {statusData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Bureau Distribution */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle>Disputes by Credit Bureau</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={bureauData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="bureau" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="count" fill="#3b82f6" />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Upcoming Deadlines and Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Clock className="h-5 w-5" />
              Upcoming Deadlines
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {upcomingDeadlines.length === 0 ? (
                <p className="text-muted-foreground">No upcoming deadlines</p>
              ) : (
                upcomingDeadlines.map(dispute => (
                  <div key={dispute.id} className="flex items-center justify-between p-3 bg-muted/50 rounded">
                    <div>
                      <h4 className="font-medium">{dispute.creditor}</h4>
                      <p className="text-sm text-muted-foreground">
                        {dispute.account} • {dispute.bureau}
                      </p>
                    </div>
                    <div className="text-right">
                      <Badge variant={dispute.priority === 'high' ? 'destructive' : 'secondary'}>
                        {dispute.priority}
                      </Badge>
                      <p className="text-xs text-muted-foreground mt-1">
                        {dispute.deadline.toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                ))
              )}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Mail className="h-5 w-5" />
              Recent Disputes
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {filteredDisputes.slice(0, 5).map(dispute => (
                <div key={dispute.id} className="flex items-center justify-between p-3 bg-muted/50 rounded">
                  <div>
                    <h4 className="font-medium">{dispute.creditor}</h4>
                    <p className="text-sm text-muted-foreground">
                      {dispute.account} • {dispute.bureau}
                    </p>
                  </div>
                  <div className="text-right">
                    <Badge variant={
                      dispute.status === 'completed' ? 'default' :
                      dispute.status === 'in_progress' ? 'secondary' :
                      dispute.status === 'pending' ? 'outline' : 'destructive'
                    }>
                      {dispute.status.replace('_', ' ')}
                    </Badge>
                    <p className="text-xs text-muted-foreground mt-1">
                      {new Date(dispute.dateUpdated).toLocaleDateString()}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default CreditDashboard;