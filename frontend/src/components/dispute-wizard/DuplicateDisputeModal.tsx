import { useNavigate } from 'react-router-dom';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { AlertTriangle, History, ArrowRight } from 'lucide-react';

interface DuplicateInfo {
  disputeId: string;
  creditorName: string;
  bureau: string;
}

interface DuplicateDisputeModalProps {
  open: boolean;
  onClose: () => void;
  onProceedAnyway: () => void;
  duplicates: DuplicateInfo[];
}

export function DuplicateDisputeModal({
  open,
  onClose,
  onProceedAnyway,
  duplicates,
}: DuplicateDisputeModalProps) {
  const navigate = useNavigate();

  const handleViewHistory = () => {
    onClose();
    navigate('/dispute-history');
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-md bg-[#111827] border border-amber-500/30 text-foreground">
        <DialogHeader>
          <div className="flex items-center gap-3 mb-1">
            <div className="flex-shrink-0 rounded-full bg-amber-500/10 p-2">
              <AlertTriangle className="h-5 w-5 text-amber-400" />
            </div>
            <DialogTitle className="text-lg font-semibold text-foreground">
              Duplicate Dispute Detected
            </DialogTitle>
          </div>
          <DialogDescription className="text-muted-foreground text-sm mt-1">
            You already filed a dispute for the following account(s) in the last 24 hours.
            Filing again may cause your dispute to be dismissed.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-2 my-2">
          {duplicates.map((d) => (
            <div
              key={d.disputeId}
              className="rounded-md border border-amber-500/20 bg-amber-500/5 px-4 py-3"
            >
              <p className="text-sm font-medium text-foreground">{d.creditorName}</p>
              <p className="text-xs text-muted-foreground mt-0.5">
                {d.bureau} &mdash; filed within the last 24 hours
              </p>
            </div>
          ))}
        </div>

        <div className="flex flex-col gap-2 mt-2">
          <Button
            onClick={handleViewHistory}
            className="btn-gold w-full flex items-center justify-center gap-2"
          >
            <History className="h-4 w-4" />
            View Dispute History
          </Button>
          <Button
            onClick={onProceedAnyway}
            variant="outline"
            className="w-full border-white/10 hover:bg-white/5 flex items-center justify-center gap-2"
          >
            Proceed Anyway
            <ArrowRight className="h-4 w-4" />
          </Button>
          <Button
            onClick={onClose}
            variant="ghost"
            className="w-full text-muted-foreground hover:text-foreground"
          >
            Cancel
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
