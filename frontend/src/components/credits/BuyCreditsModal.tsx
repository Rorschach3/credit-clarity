import React, { useState } from 'react';
import { supabase } from '@/integrations/supabase/client';
import { toast } from 'sonner';
import { Zap, Loader2 } from 'lucide-react';
import { CREDIT_PACKAGES } from '@/hooks/useCredits';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';

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
    <Dialog
      open
      onOpenChange={(open) => {
        if (!open) onClose();
      }}
    >
      <DialogContent
        className="top-4 max-h-[calc(100vh-2rem)] w-[calc(100vw-2rem)] max-w-lg translate-y-0 gap-0 overflow-hidden border border-[#1E2D47] bg-[#0F1729] p-0 shadow-2xl sm:top-[50%] sm:translate-y-[-50%] sm:rounded-xl"
      >
        {/* Header */}
        <DialogHeader className="border-b border-[#1E2D47] px-6 py-4 pr-14 text-left">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg flex items-center justify-center" style={{ background: 'rgba(212,168,83,0.15)' }}>
              <Zap className="w-5 h-5" style={{ color: '#D4A853' }} />
            </div>
            <div>
              <DialogTitle className="text-base font-bold text-white">Buy Mailing Credits</DialogTitle>
              <p className="text-xs" style={{ color: '#8892A4' }}>1 credit = $1 · Used to mail dispute letters on your behalf</p>
            </div>
          </div>
        </DialogHeader>

        <div className="max-h-[calc(100vh-8rem)] overflow-y-auto">
          {/* Context banner */}
          {creditsNeeded !== undefined && currentBalance !== undefined && (
            <div className="mx-6 mt-4 rounded-lg px-4 py-3 text-sm" style={{ background: 'rgba(220,38,38,0.1)', border: '1px solid rgba(220,38,38,0.3)', color: '#FCA5A5' }}>
              You need <strong>{creditsNeeded} credits</strong> to mail this letter. You have <strong>{currentBalance}</strong>.
              Pick a package below to top up.
            </div>
          )}

          {/* Packages */}
          <div className="grid gap-3 px-6 py-5">
            {CREDIT_PACKAGES.map((pkg) => (
              <button
                key={pkg.id}
                onClick={() => handleBuy(pkg)}
                disabled={!!purchasing}
                className="group w-full rounded-xl border p-4 text-left transition-all duration-150 hover:border-[#D4A853]"
                style={{ background: '#1A2340', borderColor: '#1E2D47' }}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-bold text-white">{pkg.label}</span>
                      {pkg.savings && (
                        <span className="rounded-full px-2 py-0.5 text-xs font-medium" style={{ background: 'rgba(212,168,83,0.2)', color: '#D4A853' }}>
                          {pkg.savings}
                        </span>
                      )}
                    </div>
                    <p className="mt-0.5 text-xs" style={{ color: '#8892A4' }}>{pkg.note}</p>
                    <div className="mt-2 flex items-center gap-1">
                      {[...Array(Math.min(pkg.credits, 12))].map((_, i) => (
                        <div key={i} className="h-2 w-2 rounded-full" style={{ background: '#D4A853', opacity: 0.7 + (i / 20) }} />
                      ))}
                      {pkg.credits > 12 && <span className="text-xs" style={{ color: '#D4A853' }}>+{pkg.credits - 12}</span>}
                    </div>
                  </div>
                  <div className="ml-4 shrink-0 text-right">
                    <div className="text-2xl font-bold text-white">${pkg.price}</div>
                    <div className="text-xs" style={{ color: '#8892A4' }}>{pkg.credits} credits</div>
                    {purchasing === pkg.id ? (
                      <Loader2 className="mt-2 ml-auto h-5 w-5 animate-spin" style={{ color: '#D4A853' }} />
                    ) : (
                      <div className="mt-2 text-xs font-semibold transition-colors group-hover:text-[#D4A853]" style={{ color: '#4A5568' }}>
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
            <div className="space-y-1 rounded-lg p-4 text-xs" style={{ background: '#1A2340', border: '1px solid #1E2D47', color: '#8892A4' }}>
              <p className="mb-2 font-semibold text-white">What each mailing costs:</p>
              <div className="flex justify-between"><span>Per printed page</span><span>1 credit</span></div>
              <div className="flex justify-between"><span>USPS Certified Mail fee</span><span>5 credits</span></div>
              <div className="mt-2 border-t pt-2" style={{ borderColor: '#1E2D47' }}>
                <div className="flex justify-between font-semibold text-white">
                  <span>Typical 5-page packet</span><span>10 credits</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};
