import React, { useState } from 'react';
import { Zap } from 'lucide-react';
import { useCredits } from '@/hooks/useCredits';
import { BuyCreditsModal } from './BuyCreditsModal';

export const CreditsBalance: React.FC = () => {
  const { balance, loading } = useCredits();
  const [showBuy, setShowBuy] = useState(false);

  if (loading) return null;

  return (
    <>
      <button
        onClick={() => setShowBuy(true)}
        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-all hover:opacity-80"
        style={{ background: 'rgba(212,168,83,0.12)', border: '1px solid rgba(212,168,83,0.25)', color: '#D4A853' }}
        title="Buy mailing credits"
      >
        <Zap className="w-3.5 h-3.5" />
        <span>{balance ?? 0} credits</span>
      </button>
      {showBuy && (
        <BuyCreditsModal
          onClose={() => setShowBuy(false)}
          currentBalance={balance ?? 0}
        />
      )}
    </>
  );
};
