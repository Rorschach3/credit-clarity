
import { CreditScoreCard } from "./CreditScoreCard";
import { RecentActivity } from "./RecentActivity";
import { DisputeSummary } from "./DisputeSummary";

interface CreditScores {
  experian: number;
  transunion: number;
  equifax: number;
}

export function Overview({ creditScores }: { creditScores: CreditScores }) {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <CreditScoreCard 
          bureau="Experian" 
          score={creditScores.experian} 
          change={12} 
          lastUpdated="14 days ago" 
        />
        
        <CreditScoreCard 
          bureau="TransUnion" 
          score={creditScores.transunion} 
          change={8} 
          lastUpdated="14 days ago" 
        />
        
        <CreditScoreCard 
          bureau="Equifax" 
          score={creditScores.equifax} 
          change={15} 
          lastUpdated="14 days ago" 
        />
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <RecentActivity />
        <DisputeSummary />
      </div>
    </div>
  );
}
