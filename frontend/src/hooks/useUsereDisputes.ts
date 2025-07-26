import { useEffect, useState } from "react";
import { supabase } from "../../supabase/client"client"";

export interface UserDispute {
  id: string;
  credit_report_id: string;
  status: "pending" | "under_review" | "resolved";
  mailing_address: string;
  created_at: string;
  modified_at?: string;
  retention_date?: string;
}

export function useUserDisputes() {
  const [disputes, setDisputes] = useState<UserDispute[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchDisputes = async () => {
      setLoading(true);
      setError(null);

      const { data, error: fetchError } = await supabase
        .from("disputes")
        .select("*")
        .order("created_at", { ascending: false });

      if (fetchError) {
        console.error("Failed to fetch disputes:", fetchError);
        setError("Unable to load disputes.");
        setDisputes([]);
        setLoading(false);
        return;
      }

      setDisputes(data as UserDispute[]);
      setLoading(false);
    };

    fetchDisputes();
  }, []);

  return { disputes, loading, error };
}
