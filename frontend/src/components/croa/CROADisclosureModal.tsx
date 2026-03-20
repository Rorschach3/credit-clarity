import React, { useState } from 'react';
import { supabase } from '@/integrations/supabase/client';
import { toast } from 'sonner';
import { ShieldCheck, X } from 'lucide-react';

interface CROADisclosureModalProps {
  userId: string;
  onAccepted: () => void;
}

export const CROADisclosureModal: React.FC<CROADisclosureModalProps> = ({ userId, onAccepted }) => {
  const [checked, setChecked] = useState(false);
  const [saving, setSaving] = useState(false);

  const handleAccept = async () => {
    if (!checked || saving) return;
    setSaving(true);
    try {
      const now = new Date().toISOString();
      const { error } = await supabase
        .from('profiles')
        .update({ croa_disclosure_accepted: true, croa_disclosure_timestamp: now })
        .eq('user_id', userId);

      if (error) throw error;
      onAccepted();
    } catch (err) {
      console.error('[CROA] Failed to save acceptance:', err);
      toast.error('Failed to save your acceptance. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="croa-title"
      style={{ background: 'rgba(0,0,0,0.75)', backdropFilter: 'blur(4px)' }}
    >
      <div
        className="relative w-full max-w-2xl rounded-xl border shadow-2xl flex flex-col max-h-[90vh]"
        style={{ background: '#0F1729', borderColor: '#1E2D47' }}
      >
        {/* Header */}
        <div className="flex items-center gap-3 px-6 py-4 border-b" style={{ borderColor: '#1E2D47' }}>
          <div className="w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0"
            style={{ background: 'rgba(212,168,83,0.15)' }}>
            <ShieldCheck className="w-5 h-5" style={{ color: '#D4A853' }} />
          </div>
          <div>
            <h2 id="croa-title" className="text-base font-700 text-white font-bold">
              Important Legal Disclosure
            </h2>
            <p className="text-xs" style={{ color: '#8892A4' }}>
              Required under the Credit Repair Organizations Act (CROA), 15 U.S.C. § 1679
            </p>
          </div>
        </div>

        {/* Scrollable body */}
        <div className="overflow-y-auto flex-1 px-6 py-5 space-y-4 text-sm" style={{ color: '#CBD5E1', lineHeight: '1.65' }}>
          <p>
            Before we generate dispute letters on your behalf, federal law requires that you receive
            and acknowledge the following disclosure.
          </p>

          <div className="rounded-lg p-4 space-y-3" style={{ background: '#1A2340', border: '1px solid #1E2D47' }}>
            <h3 className="font-semibold text-white text-sm">Your Rights Under Federal Law</h3>
            <p>
              You have a right to dispute inaccurate information in your credit report without the
              help of a credit repair organization. You may contact a consumer reporting agency
              directly to dispute the accuracy of information in your file, free of charge.
            </p>
            <p>
              Under the Fair Credit Reporting Act (FCRA), both the consumer reporting agency and the
              information provider are responsible for correcting inaccurate or incomplete information
              in your report. To protect all your rights under the law, contact the consumer reporting
              agency and the information provider directly.
            </p>
          </div>

          <div className="rounded-lg p-4 space-y-3" style={{ background: '#1A2340', border: '1px solid #1E2D47' }}>
            <h3 className="font-semibold text-white text-sm">What Credit Clarity Does and Doesn't Do</h3>
            <ul className="space-y-2 list-none">
              {[
                'Credit Clarity helps you draft and organize FCRA-compliant dispute letters.',
                'We do not guarantee any improvement to your credit score.',
                'We do not contact credit bureaus on your behalf — you send the letters yourself.',
                'We do not remove accurate, timely information from your credit report.',
                'Credit Clarity is not a law firm and does not provide legal advice.',
              ].map((item, i) => (
                <li key={i} className="flex items-start gap-2">
                  <span style={{ color: '#D4A853', marginTop: '2px', flexShrink: 0 }}>•</span>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="rounded-lg p-4 space-y-3" style={{ background: '#1A2340', border: '1px solid #1E2D47' }}>
            <h3 className="font-semibold text-white text-sm">Your CROA Rights (15 U.S.C. § 1679c)</h3>
            <p>
              Under the Credit Repair Organizations Act, you have the right to:
            </p>
            <ul className="space-y-2 list-none">
              {[
                'Cancel any contract with a credit repair organization within 3 business days.',
                'Sue a credit repair organization that violates the CROA.',
                'Obtain a copy of the "Consumer Credit File Rights Under State and Federal Law" disclosure.',
              ].map((item, i) => (
                <li key={i} className="flex items-start gap-2">
                  <span style={{ color: '#D4A853', marginTop: '2px', flexShrink: 0 }}>•</span>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </div>

          <p className="text-xs" style={{ color: '#8892A4' }}>
            This disclosure is provided pursuant to 15 U.S.C. § 1679b(a)(1) and § 1679c. By
            accepting, you confirm you have received and read this disclosure before any services
            are performed.
          </p>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t space-y-3" style={{ borderColor: '#1E2D47' }}>
          {/* Checkbox */}
          <label className="flex items-start gap-3 cursor-pointer group">
            <div className="relative flex-shrink-0 mt-0.5">
              <input
                type="checkbox"
                className="sr-only"
                checked={checked}
                onChange={e => setChecked(e.target.checked)}
                aria-label="I have read and understood the above disclosure"
              />
              <div
                className="w-5 h-5 rounded flex items-center justify-center transition-all duration-150"
                style={{
                  background: checked ? '#D4A853' : 'transparent',
                  border: `2px solid ${checked ? '#D4A853' : '#4A5568'}`,
                }}
              >
                {checked && (
                  <svg className="w-3 h-3" viewBox="0 0 12 12" fill="none">
                    <path d="M2 6l3 3 5-5" stroke="#0A0F1E" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                )}
              </div>
            </div>
            <span className="text-sm" style={{ color: checked ? '#F0F4FF' : '#8892A4' }}>
              I have read and understood the above disclosure. I understand my rights and agree to
              proceed with Credit Clarity's dispute letter assistance.
            </span>
          </label>

          {/* Accept button */}
          <button
            onClick={handleAccept}
            disabled={!checked || saving}
            className="w-full py-3 rounded-lg font-semibold text-sm transition-all duration-150"
            style={{
              background: checked && !saving
                ? 'linear-gradient(135deg, #D4A853, #E8C06A)'
                : '#1A2340',
              color: checked && !saving ? '#0A0F1E' : '#4A5568',
              cursor: checked && !saving ? 'pointer' : 'not-allowed',
              border: checked && !saving ? 'none' : '1px solid #1E2D47',
            }}
          >
            {saving ? 'Saving...' : 'I Accept — Continue to Dispute Wizard'}
          </button>

          <p className="text-center text-xs" style={{ color: '#4A5568' }}>
            This acceptance is recorded with a timestamp and is required only once.
          </p>
        </div>
      </div>
    </div>
  );
};
