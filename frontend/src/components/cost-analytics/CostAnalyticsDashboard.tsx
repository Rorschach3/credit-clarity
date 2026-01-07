import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { ChartContainer, ChartTooltip, ChartTooltipContent } from '@/components/ui/chart';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, LineChart, Line, PieChart, Pie, Cell } from 'recharts';
import { DollarSign, TrendingDown, TrendingUp, BarChart3, PieChart as PieChartIcon, AlertTriangle, CheckCircle, XCircle } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

// Types based on backend cost tracker service
interface CostEntry {
  user_id: string;
  method: 'pdfplumber' | 'pymupdf' | 'tesseract_ocr' | 'document_ai';
  file_size_mb: number;
  processing_time_ms: number;
  cost_usd: number;
  success: boolean;
  timestamp: string;
  pages_processed?: number;
  error_message?: string;
}

interface MethodStats {
  total_uses: number;
  successful_uses: number;
  total_time_ms: number;
  total_cost: number;
  avg_time_ms: number;
  success_rate: number;
  avg_cost: number;
}

interface UsageSummary {
  period_days: number;
  total_files: number;
  successful_files: number;
  overall_success_rate: number;
  total_cost_usd: number;
  avg_cost_per_file: number;
  methods: { [method: string]: MethodStats };
  cost_breakdown: { [method: string]: number };
  recommendations: string[];
}

interface CostAnalyticsDashboardProps {
  userId: string;
  className?: string;
}

const METHOD_COLORS = {
  pdfplumber: '#10b981', // green
  pymupdf: '#3b82f6',    // blue
  tesseract_ocr: '#f59e0b', // amber
  document_ai: '#ef4444'   // red
};

const METHOD_LABELS = {
  pdfplumber: 'PDF Plumber',
  pymupdf: 'PyMuPDF',
  tesseract_ocr: 'Tesseract OCR',
  document_ai: 'Document AI'
};

export const CostAnalyticsDashboard: React.FC<CostAnalyticsDashboardProps> = ({
  userId,
  className = ''
}) => {
  const [summary, setSummary] = useState<UsageSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [period, setPeriod] = useState(7); // days
  const { toast } = useToast();

  // Mock API call - replace with actual backend integration
  const fetchCostData = async (days: number) => {
    try {
      setLoading(true);
      // TODO: Replace with actual API call to backend
      // const response = await fetch(`/api/cost-analytics/summary?userId=${userId}&days=${days}`);
      // const costSummary = await response.json();

      // Mock data for demonstration
      const mockSummary: UsageSummary = {
        period_days: days,
        total_files: 45,
        successful_files: 42,
        overall_success_rate: 93.3,
        total_cost_usd: 2.85,
        avg_cost_per_file: 0.063,
        methods: {
          pdfplumber: {
            total_uses: 25,
            successful_uses: 23,
            total_time_ms: 125000,
            total_cost: 0,
            avg_time_ms: 5000,
            success_rate: 92,
            avg_cost: 0
          },
          pymupdf: {
            total_uses: 15,
            successful_uses: 14,
            total_time_ms: 85000,
            total_cost: 0,
            avg_time_ms: 5667,
            success_rate: 93.3,
            avg_cost: 0
          },
          tesseract_ocr: {
            total_uses: 3,
            successful_uses: 3,
            total_time_ms: 45000,
            total_cost: 0,
            avg_time_ms: 15000,
            success_rate: 100,
            avg_cost: 0
          },
          document_ai: {
            total_uses: 2,
            successful_uses: 2,
            total_time_ms: 12000,
            total_cost: 2.85,
            avg_time_ms: 6000,
            success_rate: 100,
            avg_cost: 1.425
          }
        },
        cost_breakdown: {
          pdfplumber: 0,
          pymupdf: 0,
          tesseract_ocr: 0,
          document_ai: 2.85
        },
        recommendations: [
          "Document AI usage is efficient but expensive. Consider optimizing free method success rates.",
          "PDF Plumber has good performance with 92% success rate.",
          "Consider implementing caching to reduce repeated processing costs."
        ]
      };

      setSummary(mockSummary);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to fetch cost analytics data',
        variant: 'destructive'
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCostData(period);
  }, [userId, period]);

  const handlePeriodChange = (newPeriod: number) => {
    setPeriod(newPeriod);
  };

  if (loading) {
    return (
      <div className={`space-y-6 ${className}`}>
        <Card>
          <CardHeader>
            <CardTitle>Cost Analytics</CardTitle>
            <CardDescription>Loading cost analytics data...</CardDescription>
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

  if (!summary) {
    return (
      <div className={`space-y-6 ${className}`}>
        <Card>
          <CardHeader>
            <CardTitle>Cost Analytics</CardTitle>
            <CardDescription>Unable to load cost analytics data</CardDescription>
          </CardHeader>
        </Card>
      </div>
    );
  }

  // Prepare chart data
  const methodPerformanceData = Object.entries(summary.methods).map(([method, stats]) => ({
    method: METHOD_LABELS[method as keyof typeof METHOD_LABELS],
    successRate: stats.success_rate,
    avgTime: stats.avg_time_ms / 1000, // Convert to seconds
    avgCost: stats.avg_cost,
    totalUses: stats.total_uses,
    color: METHOD_COLORS[method as keyof typeof METHOD_COLORS]
  }));

  const costBreakdownData = Object.entries(summary.cost_breakdown).map(([method, cost]) => ({
    method: METHOD_LABELS[method as keyof typeof METHOD_LABELS],
    cost,
    fill: METHOD_COLORS[method as keyof typeof METHOD_COLORS]
  }));

  const usageData = Object.entries(summary.methods).map(([method, stats]) => ({
    method: METHOD_LABELS[method as keyof typeof METHOD_LABELS],
    uses: stats.total_uses,
    successful: stats.successful_uses,
    failed: stats.total_uses - stats.successful_uses
  }));

  return (
    <div className={`space-y-6 ${className}`}>
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Cost Analytics</h2>
          <p className="text-muted-foreground">
            Monitor OCR processing costs and method performance
          </p>
        </div>
        <div className="flex gap-2">
          {[7, 30, 90].map((days) => (
            <Button
              key={days}
              variant={period === days ? "default" : "outline"}
              size="sm"
              onClick={() => handlePeriodChange(days)}
            >
              {days} days
            </Button>
          ))}
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Cost</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">${summary.total_cost_usd.toFixed(2)}</div>
            <p className="text-xs text-muted-foreground">
              Last {summary.period_days} days
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Cost/File</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">${summary.avg_cost_per_file.toFixed(4)}</div>
            <p className="text-xs text-muted-foreground">
              {summary.total_files} files processed
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
            <CheckCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{summary.overall_success_rate.toFixed(1)}%</div>
            <p className="text-xs text-muted-foreground">
              {summary.successful_files}/{summary.total_files} successful
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Methods Used</CardTitle>
            <BarChart3 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{Object.keys(summary.methods).length}</div>
            <p className="text-xs text-muted-foreground">
              Different OCR methods
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Recommendations */}
      {summary.recommendations.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5" />
              Recommendations
            </CardTitle>
            <CardDescription>
              Suggestions to optimize costs and improve performance
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {summary.recommendations.map((rec, index) => (
                <Alert key={index}>
                  <AlertTriangle className="h-4 w-4" />
                  <AlertDescription>{rec}</AlertDescription>
                </Alert>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      <Tabs defaultValue="performance" className="space-y-6">
        <TabsList>
          <TabsTrigger value="performance">Method Performance</TabsTrigger>
          <TabsTrigger value="costs">Cost Breakdown</TabsTrigger>
          <TabsTrigger value="usage">Usage Statistics</TabsTrigger>
        </TabsList>

        <TabsContent value="performance" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Method Performance Comparison</CardTitle>
              <CardDescription>
                Success rates, processing times, and costs by OCR method
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ChartContainer
                config={{
                  successRate: {
                    label: "Success Rate (%)",
                    color: "hsl(var(--chart-1))",
                  },
                  avgTime: {
                    label: "Avg Time (seconds)",
                    color: "hsl(var(--chart-2))",
                  },
                }}
                className="h-[400px]"
              >
                <BarChart data={methodPerformanceData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="method" />
                  <YAxis yAxisId="left" />
                  <YAxis yAxisId="right" orientation="right" />
                  <ChartTooltip content={<ChartTooltipContent />} />
                  <Bar yAxisId="left" dataKey="successRate" fill="var(--color-successRate)" name="Success Rate (%)" />
                  <Bar yAxisId="right" dataKey="avgTime" fill="var(--color-avgTime)" name="Avg Time (s)" />
                </BarChart>
              </ChartContainer>
            </CardContent>
          </Card>

          {/* Method Details Table */}
          <Card>
            <CardHeader>
              <CardTitle>Method Details</CardTitle>
              <CardDescription>Detailed statistics for each OCR method</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {Object.entries(summary.methods).map(([method, stats]) => (
                  <div key={method} className="flex items-center justify-between p-4 border rounded-lg">
                    <div className="flex items-center space-x-3">
                      <div
                        className="w-4 h-4 rounded"
                        style={{ backgroundColor: METHOD_COLORS[method as keyof typeof METHOD_COLORS] }}
                      ></div>
                      <div>
                        <p className="font-medium">{METHOD_LABELS[method as keyof typeof METHOD_LABELS]}</p>
                        <p className="text-sm text-muted-foreground">
                          {stats.total_uses} uses • {stats.success_rate.toFixed(1)}% success rate
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="font-medium">${stats.avg_cost.toFixed(4)} avg cost</p>
                      <p className="text-sm text-muted-foreground">
                        {(stats.avg_time_ms / 1000).toFixed(1)}s avg time
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="costs" className="space-y-4">
          <div className="grid gap-6 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Cost Breakdown by Method</CardTitle>
                <CardDescription>Total costs incurred by each OCR method</CardDescription>
              </CardHeader>
              <CardContent>
                <ChartContainer
                  config={{
                    cost: {
                      label: "Cost ($)",
                    },
                  }}
                  className="h-[300px]"
                >
                  <PieChart>
                    <Pie
                      data={costBreakdownData}
                      cx="50%"
                      cy="50%"
                      outerRadius={80}
                      dataKey="cost"
                      label={({ method, cost }) => cost > 0 ? `${method}: $${cost.toFixed(2)}` : null}
                    >
                      {costBreakdownData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.fill} />
                      ))}
                    </Pie>
                    <ChartTooltip content={<ChartTooltipContent />} />
                  </PieChart>
                </ChartContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Cost Efficiency</CardTitle>
                <CardDescription>Cost per successful processing</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {Object.entries(summary.methods).map(([method, stats]) => {
                    const costPerSuccess = stats.successful_uses > 0 ? stats.total_cost / stats.successful_uses : 0;
                    return (
                      <div key={method} className="flex items-center justify-between">
                        <div className="flex items-center space-x-2">
                          <div
                            className="w-3 h-3 rounded"
                            style={{ backgroundColor: METHOD_COLORS[method as keyof typeof METHOD_COLORS] }}
                          ></div>
                          <span className="text-sm">{METHOD_LABELS[method as keyof typeof METHOD_LABELS]}</span>
                        </div>
                        <div className="text-right">
                          <span className="font-medium">${costPerSuccess.toFixed(4)}</span>
                          <span className="text-xs text-muted-foreground ml-1">per success</span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="usage" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Usage Statistics</CardTitle>
              <CardDescription>Total usage and success rates by method</CardDescription>
            </CardHeader>
            <CardContent>
              <ChartContainer
                config={{
                  uses: {
                    label: "Total Uses",
                    color: "hsl(var(--chart-1))",
                  },
                  successful: {
                    label: "Successful",
                    color: "hsl(var(--chart-2))",
                  },
                  failed: {
                    label: "Failed",
                    color: "hsl(var(--chart-3))",
                  },
                }}
                className="h-[400px]"
              >
                <BarChart data={usageData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="method" />
                  <YAxis />
                  <ChartTooltip content={<ChartTooltipContent />} />
                  <Bar dataKey="successful" stackId="a" fill="var(--color-successful)" />
                  <Bar dataKey="failed" stackId="a" fill="var(--color-failed)" />
                </BarChart>
              </ChartContainer>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default CostAnalyticsDashboard;