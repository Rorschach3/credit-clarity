
import { ParsedTradeline } from './tradeline/types';

export interface GroupedTradeline {
  creditor_name: string;
  accounts: ParsedTradeline[];
  total_balance: number;
  is_negative: boolean;
}

export function groupTradelinesByAccount(tradelines: ParsedTradeline[]): GroupedTradeline[] {
  const grouped = tradelines.reduce((acc, tradeline) => {
    const key = tradeline.creditor_name || 'Unknown Creditor';
    
    if (!acc[key]) {
      acc[key] = {
        creditor_name: key,
        accounts: [],
        total_balance: 0,
        is_negative: false
      };
    }
    
    acc[key].accounts.push(tradeline);
    
    // Parse balance and add to total
    const balance = parseFloat(tradeline.account_balance?.replace(/[$,]/g, '') || '0');
    acc[key].total_balance += balance;
    
    // Mark as negative if any account is negative
    if (tradeline.is_negative) {
      acc[key].is_negative = true;
    }
    
    return acc;
  }, {} as Record<string, GroupedTradeline>);

  // Convert to array and sort by total balance (highest first)
  return Object.values(grouped).sort((a, b) => b.total_balance - a.total_balance);
}
