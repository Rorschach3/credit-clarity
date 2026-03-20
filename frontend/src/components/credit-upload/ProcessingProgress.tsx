import React from 'react';
import { Progress } from '@/components/ui/progress';
import { Loader2, Eye, Brain, CheckCircle2, XCircle } from 'lucide-react';
import { ProcessingProgress as ProcessingProgressType } from '@/utils/asyncProcessing';

interface ProcessingProgressProps {
  isProcessing: boolean;
  progress: ProcessingProgressType;
  processingMethod: 'ocr' | 'ai';
}

const STAGES = [
  { label: 'Initialize', threshold: 15 },
  { label: 'Extract',    threshold: 45 },
  { label: 'Parse',      threshold: 75 },
  { label: 'Save',       threshold: 100 },
];

export const ProcessingProgress: React.FC<ProcessingProgressProps> = ({
  isProcessing,
  progress,
  processingMethod,
}) => {
  const shouldShow = isProcessing || progress.step || progress.message;
  if (!shouldShow) return null;

  const pct = progress.progress ?? 0;
  const isCompleted = progress.step === 'Complete!' || pct >= 100;
  const isFailed = progress.step === 'Failed' || progress.step?.includes('❌');

  const borderColor = isCompleted
    ? 'border-[rgba(34,197,94,0.3)]'
    : isFailed
    ? 'border-[rgba(239,68,68,0.3)]'
    : 'border-[rgba(212,168,83,0.25)]';

  const glowBg = isCompleted
    ? 'bg-[rgba(34,197,94,0.06)]'
    : isFailed
    ? 'bg-[rgba(239,68,68,0.06)]'
    : 'bg-[rgba(212,168,83,0.04)]';

  const Icon = isCompleted
    ? CheckCircle2
    : isFailed
    ? XCircle
    : processingMethod === 'ai'
    ? Brain
    : Eye;

  const iconColor = isCompleted
    ? 'text-green-400'
    : isFailed
    ? 'text-red-400'
    : 'text-[#D4A853]';

  const label = isCompleted
    ? 'Processing Complete'
    : isFailed
    ? 'Processing Failed'
    : processingMethod === 'ai'
    ? 'AI Analysis'
    : 'OCR Extraction';

  return (
    <div
      className={`rounded-xl border ${borderColor} ${glowBg} p-5 space-y-4`}
      style={{ backdropFilter: 'blur(4px)' }}
    >
      {/* Header row */}
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2.5">
          {!isCompleted && !isFailed && isProcessing ? (
            <Loader2 className="h-4 w-4 animate-spin text-[#D4A853]" />
          ) : (
            <Icon className={`h-4 w-4 ${iconColor}`} />
          )}
          <span className="font-semibold text-sm">{label}</span>
        </div>
        <span className={`text-sm font-mono font-bold ${iconColor}`}>
          {isCompleted ? '100%' : isFailed ? 'Error' : `${pct}%`}
        </span>
      </div>

      {/* Progress bar */}
      <Progress
        value={isCompleted ? 100 : pct}
        className={`h-2 ${
          isCompleted
            ? 'bg-green-900/30 [&>[data-slot=progress-indicator]]:bg-green-400'
            : isFailed
            ? 'bg-red-900/30 [&>[data-slot=progress-indicator]]:bg-red-400'
            : 'bg-white/5 [&>[data-slot=progress-indicator]]:bg-[#D4A853]'
        }`}
      />

      {/* Current step message */}
      {progress.step && (
        <p className="text-xs text-muted-foreground leading-relaxed">
          {progress.step}
          {progress.message && progress.message !== progress.step && (
            <> &mdash; {progress.message}</>
          )}
        </p>
      )}

      {/* Stage pills */}
      <div className="flex gap-2">
        {STAGES.map(({ label: stageLabel, threshold }) => {
          const done = pct >= threshold || isCompleted;
          const active = !done && pct >= threshold - 30 && !isFailed;
          return (
            <div
              key={stageLabel}
              className={`flex-1 text-center py-1 rounded text-[10px] font-medium transition-colors ${
                done
                  ? 'bg-[rgba(34,197,94,0.15)] text-green-400'
                  : active
                  ? 'bg-[rgba(212,168,83,0.15)] text-[#D4A853]'
                  : 'bg-white/5 text-muted-foreground'
              }`}
            >
              {done ? '✓ ' : ''}{stageLabel}
            </div>
          );
        })}
      </div>
    </div>
  );
};
