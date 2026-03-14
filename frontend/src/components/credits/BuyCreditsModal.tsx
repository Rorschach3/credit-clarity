import React, { useState } from 'react';
import { supabase } from '@/integrations/supabase/client';
import { toast } from 'sonner';
import { X, Zap, CheckCircle2, Loader2 } from 'lucide-react';
import { CREDIT_PACKAGES } from '@/hooks/useCredits';

interface BuyCreditsModalProps {
  onClose: () => void;
  /** If set, shown as "you need X more credits" context */
  creditsNeeded?: number;
  currentBalance?: number;
}

export const BuyCreditsModal: React.FC<BuyCreditsModalProps> = ({
  onClose,
  creditsNeeded,
  currentBalance,
}) => {
  const [purchasing, setPurchasing] = useState<string | null>(null);

  const handleBuy = async (pkg: typeof CREDIT_PACKAGES[number]) => {
    setPurchasing(pkg.id);
    try {
      const { data, error } = await supabase.functions.invoke('create-checkout', {
        body: { priceId: pkg.id, mode: 'payment', credits: pkg.credits },
      });
      if (error) throw error;
      if (data?.url) {
        window.location.href = data.url;
      } else {
        throw new Error('No checkout URL returned');
      }
    } catch (err) {
      console.error('[BuyCreditsModal] checkout error:', err);
      toast.error('Failed to start checkout. Please try again.');
      setPurchasing(null);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{ background: 'rgba(0,0,0,0.75)', backdropFilter: 'blur(4px)' }}
    >
      <div
        className="relative w-full max-w-lg rounded-xl border shadow-2xl"
        style={{ background: '#0F1729', borderColor: '#1E2D47' }}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b" style={{ borderColor: '#1E2D47' }}>
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg flex items-center justify-center" style={{ background: 'rgba(212,168,83,0.15)' }}>
              <Zap className="w-5 h-5" style={{ color: '#D4A853' }} />
            </div>
            <div>
              <h2 className="text-base font-bold text-white">Buy Mailing Credits</h2>
              <p className="text-xs" style={{ color: '#8892A4' }}>1 credit = $1 · Used to mail dispute letters on your behalf</p>
            </div>
          </div>
          <button onClick={onClose} className="text-muted-foreground hover:text-white transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Context banner */}
        {creditsNeeded !== undefined && currentBalance !== undefined && (
          <div className="mx-6 mt-4 px-4 py-3 rounded-lg text-sm" style={{ background: 'rgba(220,38,38,0.1)', border: '1px solid rgba(220,38,38,0.3)', color: '#FCA5A5' }}>
            You need <strong>{creditsNeeded} credits</strong> to mail this letter. You have <strong>{currentBalance}</strong>.
            Pick a package below to top up.
          </div>
        )}

        {/* Packages */}
        <div className="px-6 py-5 grid gap-3">
          {CREDIT_PACKAGES.map((pkg) => (
            <button
              key={pkg.id}
              onClick={() => handleBuy(pkg)}
              disabled={!!purchasing}
              className="w-full text-left rounded-xl border p-4 transition-all duration-150 hover:border-[#D4A853] group"
              style={{ background: '#1A2340', borderColor: '#1E2D47' }}
            >
              <div className="flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-white text-sm">{pkg.label}</span>
                    {pkg.savings && (
                      <span className="text-xs px-2 py-0.5 rounded-full font-medium" style={{ background: 'rgba(212,168,83,0.2)', color: '#D4A853' }}>
                        {pkg.savings}
                      </span>
                    )}
                  </div>
                  <p className="text-xs mt-0.5" style={{ color: '#8892A4' }}>{pkg.note}</p>
                  <div className="flex items-center gap-1 mt-2">
                    {[...Array(Math.min(pkg.credits, 12))].map((_, i) => (
                      <div key={i} className="w-2 h-2 rounded-full" style={{ background: '#D4A853', opacity: 0.7 + (i / 20) }} />
                    ))}
                    {pkg.credits > 12 && <span className="text-xs" style={{ color: '#D4A853' }}>+{pkg.credits - 12}</span>}
                  </div>
                </div>
                <div className="text-right shrink-0 ml-4">
                  <div className="text-2xl font-bold text-white">${pkg.price}</div>
                  <div className="text-xs" style={{ color: '#8892A4' }}>{pkg.credits} credits</div>
                  {purchasing === pkg.id ? (
                    <Loader2 className="w-5 h-5 animate-spin mt-2 ml-auto" style={{ color: '#D4A853' }} />
                  ) : (
                    <div className="mt-2 text-xs font-semibold group-hover:text-[#D4A853] transition-colors" style={{ color: '#4A5568' }}>
                      Buy →
                    </div>
                  )}
                </div>
              </div>
            </button>
          ))}
        </div>

        {/* What credits cover */}
        <div className="px-6 pb-5">
          <div className="rounded-lg p-4 text-xs space-y-1" style={{ background: '#1A2340', border: '1px solid #1E2D47', color: '#8892A4' }}>
            <p className="font-semibold text-white mb-2">What each mailing costs:</p>
            <div className="flex justify-between"><span>Per printed page</span><span>1 credit</span></div>
            <div className="flex justify-between"><span>USPS Certified Mail fee</span><span>5 credits</span></div>
            <div className="border-t mt-2 pt-2" style={{ borderColor: '#1E2D47' }}>
              <div className="flex justify-between font-semibold text-white">
                <span>Typical 5-page packet</span><span>10 credits</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
