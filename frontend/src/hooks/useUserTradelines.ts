import { useEffect, useState } from "react";
import { supabase } from "../../supabase/client";
import { useAuth } from "@/hooks/use-auth";

export interface Tradeline {
  id: string;
  creditorName: string;
  accountNumber: string;
  accountStatus: string;
  isNegative: boolean;
  negativeReason: string | null;
  accountBalance: number;
  date_opened: string;
  accountCondition: string;
  credit_bureau: string;
  credit_limit: string;
  monthly_payment: string;
  created_at: string;
  accountType: string;
  status: string;
}

interface SupabaseTradelineRow {
  id?: string;
  user_id?: string;
  creditor_name?: string;
  account_number?: string;
  account_status?: string;
  account_type?: string;
  account_balance?: number;
  date_opened?: string;
  credit_limit?: string;
  monthly_payment?: string;
  credit_bureau?: string;
  created_at?: string;
  isNegative?: boolean;
}

export function useUserTradelines() {
  const [tradelines, setTradelines] = useState<Tradeline[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const { user } = useAuth();

  useEffect(() => {
    const fetchTradelines = async () => {
      setLoading(true);
      setError(null);

      if (!user) {
        console.warn("User not logged in, cannot fetch tradelines.");
        setTradelines([]);
        setLoading(false);
        return;
      }

      const { data, error: supabaseError } = await supabase
        .from("tradelines")
        .select("*")
        .eq("user_id", user.id)
        .order("date_opened", { ascending: false });

      if (supabaseError) {
        console.error("Failed to fetch tradelines:", supabaseError.message);
        setError("Failed to fetch tradelines.");
        setTradelines([]);
        setLoading(false);
        return;
      }
      const formatted: Tradeline[] = data.map((item) => {
        const negativeReason = item.isNegative ? (/collection|charge.?off|late/i.exec(item.account_status)?.[0] ?? null) : null;

        return {
          id: item.id ?? "",
          creditorName: item.creditor_name ?? "",
          accountNumber: item.account_number ?? "",
          accountStatus: item.account_status ?? "",
          isNegative: item.isNegative ?? false,
          negativeReason: negativeReason,
          accountBalance: item.account_balance ?? 0,
          date_opened: item.date_opened ?? "",
          credit_bureau: item.credit_bureau ?? "",
          credit_limit: item.credit_limit ?? "",
          monthlyPayment: item.monthly_payment ?? "",
          created_at: item.created_at ?? "",
          accountCondition: "",
          accountType: item.account_type ?? "",
          status: item.account_status ?? "",
        };
      });

      setTradelines(formatted);
      setLoading(false);
    };

    fetchTradelines();
  }, [user]);

  return { tradelines, loading, error };
}
