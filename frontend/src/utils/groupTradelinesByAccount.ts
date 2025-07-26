export type Bureau = "equifax" | "transunion" | "experian";

export interface BureauTradeline {
  accountName: string;
  accountNumber: string;
  status?: string;
  dateOpened?: string;
  balance?: number;
  type?: string;
  creditLimit?: number;
  monthlyPayment?: number;
  disputeCount?: number;
  creditBureau: Bureau;
}

export interface GroupedTradeline {
  key: string; // e.g., `${accountName}|${accountNumber}`
  equifax?: BureauTradeline;
  transunion?: BureauTradeline;
  experian?: BureauTradeline;
}

export function groupTradelinesByAccount(
  tradelines: BureauTradeline[]
): GroupedTradeline[] {
  const map = new Map<string, GroupedTradeline>();

  tradelines.forEach((t) => {
    const key = `${t.accountName}|${t.accountNumber}`;
    if (!map.has(key)) {
      map.set(key, { key });
    }
    const group = map.get(key)!;
    if (t.creditBureau === "equifax") group.equifax = t;
    if (t.creditBureau === "transunion") group.transunion = t;
    if (t.creditBureau === "experian") group.experian = t;
  });

  return Array.from(map.values());
}