
export interface NegativeItem {
  id: string;
  creditorName: string;
  accountNumber: string;
  accountType: string;
  balance: number;
  status: string;
  bureaus: string[];
  isNegative: boolean;
  recommendedReason?: string;
  amount: string;
  dateReported: string;
  reason: string;
}
