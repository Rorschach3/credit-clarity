
import React, { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { FileText, AlertTriangle } from 'lucide-react';
import { supabase } from '@/integrations/supabase/client';
import { useAuth } from '@/hooks/use-auth';
import { useToast } from '@/hooks/use-toast';

interface DisputeItem {
  id: string;
  bureau: string;
  company: string;
  type: string;
  amount: string;
  status: string;
}

interface NegativeItemsDialogProps {
  trigger?: React.ReactNode;
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
}

export function NegativeItemsDialog({ trigger, open, onOpenChange }: NegativeItemsDialogProps) {
  const [disputes, setDisputes] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const { user } = useAuth();
  const { toast } = useToast();

  useEffect(() => {
    if (user?.id) {
      fetchDisputes();
    }
  }, [user]);

  const fetchDisputes = async () => {
    try {
      const { data, error } = await supabase
        .from('disputes')
        .select('*')
        .eq('user_id', user?.id || '');

      if (error) throw error;

      setDisputes(data || []);
    } catch (error) {
      console.error('Error fetching disputes:', error);
      toast({
        title: "Error",
        description: "Failed to load disputes",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const disputeItems: DisputeItem[] = disputes.map((dispute) => ({
    id: dispute.id,
    bureau: dispute.credit_report_id,
    company: dispute.mailing_address.split('\n')[0] || 'Unknown',
    type: 'Credit Report Dispute',
    amount: 'N/A',
    status: dispute.status
  }));

  const negativeCount = disputeItems.filter(item => 
    item.status === 'pending' || item.status === 'in_progress'
  ).length;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogTrigger asChild>
        {trigger || (
          <Button variant="outline" className="w-full">
            <AlertTriangle className="w-4 h-4 mr-2" />
            View Negative Items ({negativeCount})
          </Button>
        )}
      </DialogTrigger>
      <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <FileText className="w-5 h-5" />
            Negative Items & Disputes
          </DialogTitle>
        </DialogHeader>
        
        <div className="space-y-4">
          {loading ? (
            <div className="flex justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
          ) : disputeItems.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-muted-foreground">No disputes found.</p>
            </div>
          ) : (
            <div className="grid gap-4">
              {disputeItems.map((item) => (
                <Card key={item.id}>
                  <CardHeader className="pb-2">
                    <div className="flex justify-between items-start">
                      <CardTitle className="text-lg">{item.company}</CardTitle>
                      <Badge variant={
                        item.status === 'pending' ? 'secondary' :
                        item.status === 'in_progress' ? 'default' :
                        item.status === 'resolved' ? 'default' : 'destructive'
                      }>
                        {item.status}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div>
                        <p className="font-medium text-muted-foreground">Bureau</p>
                        <p>{item.bureau}</p>
                      </div>
                      <div>
                        <p className="font-medium text-muted-foreground">Type</p>
                        <p>{item.type}</p>
                      </div>
                      <div>
                        <p className="font-medium text-muted-foreground">Amount</p>
                        <p>{item.amount}</p>
                      </div>
                      <div>
                        <p className="font-medium text-muted-foreground">Status</p>
                        <p className="capitalize">{item.status}</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
