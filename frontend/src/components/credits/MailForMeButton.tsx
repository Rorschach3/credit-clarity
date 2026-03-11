import React, { useState } from 'react';
import { supabase } from '@/integrations/supabase/client';
import { toast } from 'sonner';
import { Mail, Loader2, Zap, CheckCircle2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useCredits, estimatePageCount, calcMailingCost } from '@/hooks/useCredits';
import { BuyCreditsModal } from './BuyCreditsModal';

interface MailForMeButtonProps {
  disputeId: string;
  bureau: string;
  letterText: string;
  fromAddress: {
    name: string;
    address_line1: string;
    address_city: string;
    address_state: string;
    address_zip: string;
  };
  docCount?: number;
  alreadyMailed?: boolean;
  onMailed: (letterId: string) => void;
}

export const MailForMeButton: React.FC<MailForMeButtonProps> = ({
  disputeId,
  bureau,
  letterText,
  fromAddress,
  docCount = 0,
  alreadyMailed,
  onMailed,
}) => {
  const { balance, deduct, fetchBalance } = useCredits();
  const [step, setStep] = useState<'idle' | 'confirm' | 'mailing'>('idle');
  const [showBuyCredits, setShowBuyCredits] = useState(false);

  const pageCount = estimatePageCount(letterText, docCount);
  const cost = calcMailingCost(pageCount);
  const canAfford = (balance ?? 0) >= cost;

  if (alreadyMailed) {
    return (
      <span className="h-7 flex items-center gap-1 text-xs text-green-400 px-1">
        <CheckCircle2 className="h-3.5 w-3.5" />
        Mailed
      </span>
    );
  }

  const handleConfirm = async () => {
    setStep('mailing');

    const ok = await deduct(cost, `Certified mailing to ${bureau} — ${pageCount} pages`, disputeId);
    if (!ok) {
      toast.error('Credit deduction failed. Please try again.');
      setStep('idle');
      return;
    }

    try {
      const { data, error } = await supabase.functions.invoke('mail-letter', {
        body: { bureau, letterContent: letterText, fromAddress },
      });
      if (error) throw error;

      toast.success(`Letter mailed to ${bureau}!`, {
        description: data?.expectedDelivery
          ? `Est. delivery: ${new Date(data.expectedDelivery).toLocaleDateString()}`
          : 'Letter is being processed.',
      });
      onMailed(data?.letterId ?? 'sent');
    } catch (err) {
      console.error('[MailForMeButton] mailing error:', err);
      // Refund credits on failure
      await supabase.from('credit_transactions').insert({
        user_id: (await supabase.auth.getUser()).data.user?.id ?? '',
        amount: cost,
        type: 'refund',
        description: `Refund — mailing to ${bureau} failed`,
        letter_id: disputeId,
      });
      await fetchBalance();
      toast.error('Mailing failed — credits refunded.');
      setStep('idle');
    }
  };

  // Confirm dialog
  if (step === 'confirm') {
    return (
      <div className="flex items-center gap-2 flex-wrap">
        <span className="text-xs" style={{ color: '#8892A4' }}>
          Cost: <strong style={{ color: '#D4A853' }}>{cost} credits</strong>
          <span className="ml-1" style={{ color: '#4A5568' }}>({pageCount} pages + certified)</span>
        </span>
        <Button
          size="sm"
          className="h-7 text-xs px-2 bg-[#D4A853] hover:bg-[#E8C06A] text-[#0A0F1E] font-semibold border-0"
          onClick={handleConfirm}
        >
          Confirm
        </Button>
        <Button
          variant="ghost"
          size="sm"
          className="h-7 text-xs px-2"
          onClick={() => setStep('idle')}
        >
          Cancel
        </Button>
        {showBuyCredits && (
          <BuyCreditsModal
            onClose={() => { setShowBuyCredits(false); fetchBalance(); }}
            creditsNeeded={cost - (balance ?? 0)}
            currentBalance={balance ?? 0}
          />
        )}
      </div>
    );
  }

  if (step === 'mailing') {
    return (
      <Button size="sm" disabled className="h-7 text-xs px-2">
        <Loader2 className="h-3.5 w-3.5 mr-1 animate-spin" />
        Mailing…
      </Button>
    );
  }

  // Idle — show Mail for Me button
  return (
    <>
      <Button
        size="sm"
        className="h-7 text-xs px-2 font-semibold border-0"
        style={{
          background: canAfford
            ? 'linear-gradient(135deg, #D4A853, #E8C06A)'
            : '#1A2340',
          color: canAfford ? '#0A0F1E' : '#D4A853',
          border: canAfford ? 'none' : '1px solid rgba(212,168,83,0.4)',
        }}
        onClick={() => {
          if (!canAfford) { setShowBuyCredits(true); return; }
          setStep('confirm');
        }}
      >
        {canAfford ? (
          <><Mail className="h-3.5 w-3.5 mr-1" />Mail for Me</>
        ) : (
          <><Zap className="h-3.5 w-3.5 mr-1" />Buy Credits</>
        )}
      </Button>
      {showBuyCredits && (
        <BuyCreditsModal
          onClose={() => { setShowBuyCredits(false); fetchBalance(); }}
          creditsNeeded={cost - (balance ?? 0)}
          currentBalance={balance ?? 0}
        />
      )}
    </>
  );
};
