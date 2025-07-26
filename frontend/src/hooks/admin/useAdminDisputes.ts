import { useEffect, useState } from "react";
import { supabase } from "../../../supabase/client";

export interface AdminDisputeEntry {
  id: string;
  user_id: string;
  letter_content: string;
  status: string;
  created_at: string;
  email?: string;
}

export function useAdminDisputes() {
  const [disputes, setDisputes] = useState<AdminDisputeEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchDisputes = async () => {
      setLoading(true);
      const { data: session } = await supabase.auth.getUser();
      const user = session?.user;

      if (!user) {
        setError("Not authenticated");
        setLoading(false);
        return;
      }

      const { data, error } = await supabase
        .from("disputes")
        .select("id, user_id, letter_content, status, created_at, profiles:profiles(email)")
        .order("created_at", { ascending: false });

      if (error) {
        setError(error.message);
        setLoading(false);
        return;
      }

      const formatted = (data || []).map((entry: any) => ({
        id: entry.id,
        user_id: entry.user_id,
        letter_content: entry.letter_content,
        status: entry.status,
        created_at: entry.created_at,
        email: entry.profiles?.email ?? "",
      }));

      setDisputes(formatted);
      setLoading(false);
    };

    fetchDisputes();
  }, []);

  return { disputes, loading, error };
}
