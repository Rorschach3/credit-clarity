
import { Progress } from "@/components/ui/progress";
import { Card, CardHeader, CardContent, CardTitle, CardDescription } from "@/components/ui/card";

interface CreditScoreCardProps {
  bureau: string;
  score: number;
  change: number;
  lastUpdated: string;
}

export function CreditScoreCard({ bureau, score, change, lastUpdated }: CreditScoreCardProps) {
  // Calculate progress percentage (assuming scores range from 300-850)
  const progressValue = ((score - 300) / (850 - 300)) * 100;
  
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-lg">{bureau}</CardTitle>
        <CardDescription>Last updated: {lastUpdated}</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex items-end space-x-2">
          <span className="text-3xl font-bold text-brand-600">{score}</span>
          <span className={`text-sm ${change >= 0 ? 'text-green-600' : 'text-red-600'} pb-1`}>
            {change >= 0 ? '+' : ''}{change} pts
          </span>
        </div>
        <Progress value={progressValue} className="h-2 mt-2" />
      </CardContent>
    </Card>
  );
}
