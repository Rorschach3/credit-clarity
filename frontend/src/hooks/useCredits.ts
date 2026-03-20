import { useState, useEffect, useCallback } from 'react';
import { supabase } from '@/integrations/supabase/client';
import { useAuth } from '@/hooks/use-auth';

export const CERTIFIED_MAIL_CREDITS = 5;  // USPS certified mail fee
export const PER_PAGE_CREDITS = 1;         // per printed page

export const CREDIT_PACKAGES = [
  { id: 'credits_15',  credits: 15,  price: 15, label: 'Starter',  note: '~1 bureau mailing',         savings: null },
  { id: 'credits_35',  credits: 35,  price: 30, label: 'Value',    note: '~3 bureau mailings',        savings: 'Save $5' },
  { id: 'credits_60',  credits: 60,  price: 50, label: 'Pro',      note: '~5+ bureau mailings',       savings: 'Save $10' },
] as const;

/** Estimate page count from letter text + number of supporting documents */
export const estimatePageCount = (letterText: string, docCount = 0): number => {
  const charsPerPage = 3000;
  const letterPages = Math.max(1, Math.ceil(letterText.length / charsPerPage));
  return letterPages + docCount; // 1 page per supporting doc (ID, SSN, utility bill)
};

/** Calculate mailing cost in credits */
export const calcMailingCost = (pageCount: number): number =>
  pageCount * PER_PAGE_CREDITS + CERTIFIED_MAIL_CREDITS;

export const useCredits = () => {
  const { user } = useAuth();
  const [balance, setBalance] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchBalance = useCallback(async () => {
    if (!user?.id) { setBalance(null); setLoading(false); return; }

    const { data } = await supabase
      .from('user_credits')
      .select('balance')
      .eq('user_id', user.id)
      .maybeSingle();

    setBalance(data?.balance ?? 0);
    setLoading(false);
  }, [user?.id]);

  useEffect(() => { fetchBalance(); }, [fetchBalance]);

  const deduct = useCallback(async (amount: number, description: string, letterId?: string): Promise<boolean> => {
    if (!user?.id || balance === null || balance < amount) return false;

    const { error } = await supabase.rpc('deduct_credits', {
      p_user_id: user.id,
      p_amount: amount,
      p_description: description,
      p_letter_id: letterId ?? null,
    });

    if (error) { console.error('[useCredits] deduct error:', error); return false; }
    setBalance((b) => (b ?? 0) - amount);
    return true;
  }, [user?.id, balance]);

  return { balance, loading, fetchBalance, deduct };
};
