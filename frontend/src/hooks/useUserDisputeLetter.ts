import { useEffect, useState } from "react";
import { supabase } from "../../supabase/client";

export interface DisputeLetter {
  id: string;
  first_name: string;
  last_name: string;
  address: string;
  city: string;
  state: string;
  zip: string;
  email: string;
  tradelines: {
    creditorName: string;
    accountNumber: string;
    status: string;
    negativeReason?: string;
  }[];
  created_on: string;
}

export function useUserDisputeLetters() {
  const [letters, setLetters] = useState<DisputeLetter[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchLetters = async () => {
      setLoading(true);
      const { data, error: supabaseError } = await supabase
        .from("disputes")
        .select("*")
        .order("created_on", { ascending: false });

      if (supabaseError) {
        console.error("Failed to fetch dispute letters:", supabaseError.message);
        setError("Unable to load dispute letters.");
        setLetters([]);
      } else {
        setLetters(data || []);
      }

      setLoading(false);
    };

    fetchLetters();
  }, []);

  return { letters, loading, error };
}
