import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { ChartContainer, ChartTooltip, ChartTooltipContent } from '@/components/ui/chart';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell } from 'recharts';
import { RefreshCw, AlertTriangle, TrendingUp, Shield, Eye } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

// Types based on backend service
interface CreditChange {
  change_id: string;
  user_id: string;
  change_type: 'new_account' | 'account_closed' | 'balance_change' | 'status_change' | 'score_change' | 'new_inquiry' | 'address_change' | 'personal_info_change' | 'dispute_update' | 'fraud_alert';
  severity: 'low' | 'medium' | 'high' | 'critical';
  title: string;
  description: string;
  old_value?: string;
  new_value?: string;
  bureau: string;
  detected_at: string;
  account_number?: string;
  creditor_name?: string;
  amount?: number;
  score_impact?: number;
}

interface CreditScore {
  score: number;
  bureau: string;
  model: string;
  date: string;
  factors: string[];
}

interface MonitoringStatus {
  service_name: string;
  is_connected: boolean;
  last_check: string;
  user_enrolled: boolean;
  subscription_status: string;
  next_update?: string;
  error_message?: string;
}

interface CreditMonitoringData {
  changes: CreditChange[];
  scores: { [provider: string]: CreditScore[] };
  status: MonitoringStatus[];
  last_updated: string;
}

interface CreditMonitoringDashboardProps {
  userId: string;
  className?: string;
}

const SEVERITY_COLORS = {
  low: 'bg-blue-100 text-blue-800',
  medium: 'bg-yellow-100 text-yellow-800',
  high: 'bg-orange-100 text-orange-800',
  critical: 'bg-red-100 text-red-800'
};

const CHANGE_TYPE_ICONS = {
  new_account: TrendingUp,
  account_closed: AlertTriangle,
  balance_change: TrendingUp,
  status_change: AlertTriangle,
  score_change: TrendingUp,
  new_inquiry: Eye,
  address_change: Shield,
  personal_info_change: Shield,
  dispute_update: AlertTriangle,
  fraud_alert: AlertTriangle
};

export const CreditMonitoringDashboard: React.FC<CreditMonitoringDashboardProps> = ({
  userId,
  className = ''
}) => {
  const [data, setData] = useState<CreditMonitoringData | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const { toast } = useToast();

  // Mock API call - replace with actual backend integration
  const fetchMonitoringData = async (forceRefresh = false) => {
    try {
      setRefreshing(forceRefresh);
      // TODO: Replace with actual API call to backend
      // const response = await fetch(`/api/users/${userId}/credit-monitoring`);
      // const monitoringData = await response.json();

      // Mock data for demonstration
      const mockData: CreditMonitoringData = {
        changes: [
          {
            change_id: '1',
            user_id: userId,
            change_type: 'balance_change',
            severity: 'medium',
            title: 'Balance Increased',
            description: 'Balance changed on Chase Credit Card',
            old_value: '$1,250.00',
            new_value: '$1,450.00',
            bureau: 'TransUnion',
            detected_at: new Date(Date.now() - 86400000).toISOString(),
            account_number: '****1234',
            creditor_name: 'Chase',
            amount: 200
          },
          {
            change_id: '2',
            user_id: userId,
            change_type: 'score_change',
            severity: 'low',
            title: 'Credit Score Improved',
            description: 'Your TransUnion score increased by 5 points',
            old_value: '725',
            new_value: '730',
            bureau: 'TransUnion',
            detected_at: new Date(Date.now() - 172800000).toISOString(),
            score_impact: 5
          }
        ],
        scores: {
          creditkarma: [
            {
              score: 730,
              bureau: 'TransUnion',
              model: 'VantageScore 3.0',
              date: new Date().toISOString(),
              factors: ['Payment history', 'Credit utilization', 'Length of credit history']
            }
          ]
        },
        status: [
          {
            service_name: 'Credit Karma',
            is_connected: true,
            last_check: new Date().toISOString(),
            user_enrolled: true,
            subscription_status: 'active'
          },
          {
            service_name: 'Experian',
            is_connected: false,
            last_check: new Date(Date.now() - 3600000).toISOString(),
            user_enrolled: false,
            subscription_status: 'inactive',
            error_message: 'API key not configured'
          }
        ],
        last_updated: new Date().toISOString()
      };

      setData(mockData);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to fetch credit monitoring data',
        variant: 'destructive'
      });
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchMonitoringData();
  }, [userId]);

  const handleRefresh = () => {
    fetchMonitoringData(true);
  };

  const handleEnrollProvider = async (providerName: string) => {
    // TODO: Implement provider enrollment
    toast({
      title: 'Enrollment',
      description: `Enrollment for ${providerName} would be implemented here`,
    });
  };

  if (loading) {
    return (
      <div className={`space-y-6 ${className}`}>
        <Card>
          <CardHeader>
            <CardTitle>Credit Monitoring</CardTitle>
            <CardDescription>Loading your credit monitoring data...</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="animate-pulse space-y-4">
              <div className="h-4 bg-gray-200 rounded w-3/4"></div>
              <div className="h-4 bg-gray-200 rounded w-1/2"></div>
              <div className="h-32 bg-gray-200 rounded"></div>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!data) {
    return (
      <div className={`space-y-6 ${className}`}>
        <Card>
          <CardHeader>
            <CardTitle>Credit Monitoring</CardTitle>
            <CardDescription>Unable to load credit monitoring data</CardDescription>
          </CardHeader>
        </Card>
      </div>
    );
  }

  // Prepare chart data
  const scoreChartData = Object.entries(data.scores).flatMap(([provider, scores]) =>
    scores.map(score => ({
      date: new Date(score.date).toLocaleDateString(),
      score: score.score,
      bureau: score.bureau,
      provider
    }))
  );

  const changesByType = data.changes.reduce((acc, change) => {
    acc[change.change_type] = (acc[change.change_type] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const changeTypeData = Object.entries(changesByType).map(([type, count]) => ({
    type: type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()),
    count,
    fill: `hsl(${Math.random() * 360}, 70%, 50%)`
  }));

  return (
    <div className={`space-y-6 ${className}`}>
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Credit Monitoring</h2>
          <p className="text-muted-foreground">
            Monitor your credit reports and receive alerts about important changes
          </p>
        </div>
        <Button
          onClick={handleRefresh}
          disabled={refreshing}
          variant="outline"
        >
          <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Service Status */}
      <Card>
        <CardHeader>
          <CardTitle>Monitoring Services</CardTitle>
          <CardDescription>Status of your credit monitoring providers</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2">
            {data.status.map((status) => (
              <div key={status.service_name} className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex items-center space-x-3">
                  <div className={`w-3 h-3 rounded-full ${status.is_connected ? 'bg-green-500' : 'bg-red-500'}`}></div>
                  <div>
                    <p className="font-medium">{status.service_name}</p>
                    <p className="text-sm text-muted-foreground">
                      {status.user_enrolled ? 'Enrolled' : 'Not enrolled'}
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  {status.is_connected ? (
                    <Badge variant="secondary">Connected</Badge>
                  ) : (
                    <Button
                      size="sm"
                      onClick={() => handleEnrollProvider(status.service_name)}
                    >
                      Enroll
                    </Button>
                  )}
                  {status.error_message && (
                    <p className="text-xs text-red-600 mt-1">{status.error_message}</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Tabs defaultValue="changes" className="space-y-6">
        <TabsList>
          <TabsTrigger value="changes">Recent Changes</TabsTrigger>
          <TabsTrigger value="scores">Credit Scores</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
        </TabsList>

        <TabsContent value="changes" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Recent Credit Changes</CardTitle>
              <CardDescription>
                Latest changes detected in your credit reports
              </CardDescription>
            </CardHeader>
            <CardContent>
              {data.changes.length === 0 ? (
                <p className="text-muted-foreground">No recent changes detected</p>
              ) : (
                <div className="space-y-4">
                  {data.changes.map((change) => {
                    const IconComponent = CHANGE_TYPE_ICONS[change.change_type] || AlertTriangle;
                    return (
                      <Alert key={change.change_id}>
                        <IconComponent className="h-4 w-4" />
                        <AlertDescription>
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <div className="flex items-center gap-2 mb-1">
                                <h4 className="font-medium">{change.title}</h4>
                                <Badge className={SEVERITY_COLORS[change.severity]}>
                                  {change.severity}
                                </Badge>
                              </div>
                              <p className="text-sm text-muted-foreground mb-2">
                                {change.description}
                              </p>
                              {change.old_value && change.new_value && (
                                <p className="text-sm">
                                  <span className="text-red-600">{change.old_value}</span>
                                  {' → '}
                                  <span className="text-green-600">{change.new_value}</span>
                                </p>
                              )}
                              <p className="text-xs text-muted-foreground">
                                {change.bureau} • {new Date(change.detected_at).toLocaleString()}
                              </p>
                            </div>
                          </div>
                        </AlertDescription>
                      </Alert>
                    );
                  })}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="scores" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Credit Scores</CardTitle>
              <CardDescription>Your current credit scores from monitoring providers</CardDescription>
            </CardHeader>
            <CardContent>
              {Object.keys(data.scores).length === 0 ? (
                <p className="text-muted-foreground">No credit scores available</p>
              ) : (
                <div className="space-y-6">
                  {Object.entries(data.scores).map(([provider, scores]) => (
                    <div key={provider}>
                      <h3 className="font-medium mb-4 capitalize">{provider}</h3>
                      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                        {scores.map((score, index) => (
                          <Card key={index}>
                            <CardContent className="pt-6">
                              <div className="text-center">
                                <div className="text-3xl font-bold text-blue-600">{score.score}</div>
                                <p className="text-sm text-muted-foreground">{score.bureau}</p>
                                <p className="text-xs text-muted-foreground">{score.model}</p>
                                <p className="text-xs text-muted-foreground mt-2">
                                  {new Date(score.date).toLocaleDateString()}
                                </p>
                              </div>
                            </CardContent>
                          </Card>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="analytics" className="space-y-4">
          <div className="grid gap-6 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Credit Score Trend</CardTitle>
                <CardDescription>Score changes over time</CardDescription>
              </CardHeader>
              <CardContent>
                <ChartContainer
                  config={{
                    score: {
                      label: "Credit Score",
                      color: "hsl(var(--chart-1))",
                    },
                  }}
                  className="h-[300px]"
                >
                  <LineChart data={scoreChartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <ChartTooltip content={<ChartTooltipContent />} />
                    <Line
                      type="monotone"
                      dataKey="score"
                      stroke="var(--color-score)"
                      strokeWidth={2}
                    />
                  </LineChart>
                </ChartContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Change Types</CardTitle>
                <CardDescription>Distribution of credit changes</CardDescription>
              </CardHeader>
              <CardContent>
                <ChartContainer
                  config={{
                    count: {
                      label: "Count",
                    },
                  }}
                  className="h-[300px]"
                >
                  <PieChart>
                    <Pie
                      data={changeTypeData}
                      cx="50%"
                      cy="50%"
                      outerRadius={80}
                      dataKey="count"
                      label={({ type, count }) => `${type}: ${count}`}
                    >
                      {changeTypeData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.fill} />
                      ))}
                    </Pie>
                    <ChartTooltip content={<ChartTooltipContent />} />
                  </PieChart>
                </ChartContainer>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default CreditMonitoringDashboard;