export interface NegativeItem {
  id: string;
  creditorName: string;
  accountNumber: string;
  accountBalance: string;
  dateReported: string;
  creditBureau: string;
  accountType: string;
  accountStatus: string;
}

export interface CreditReport {
  id: string;
  bureau: string;
  uploadDate: string;
  fileUrl: string;
  fileName: string;
  tradelineData?: {
    creditorName: string;
    accountNumber: string;
    paymentHistory: string;
    creditLimit: string;
    currentBalance: string;
  };
}
