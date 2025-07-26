import { useEffect, useState } from 'react';
import { supabase } from '../../../supabase/client';
import type { Tables as TablesType } from '../../../supabase/types/supabase';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { FileText } from "lucide-react";

type Dispute = TablesType<'disputes'>;

function getStatusBadge(status: string) {
  switch (status) {
    case 'pending':
      return <Badge variant="outline" className="flex items-center gap-1"><FileText className="h-3 w-3" /> Pending</Badge>;
    default:
      return <Badge variant="outline">{status}</Badge>;
  }
}

const RealTimeQueue = () => {
  const [pendingDisputes, setPendingDisputes] = useState<Dispute[] | null>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    setIsLoading(true);
    const fetchPendingDisputes = async () => {
      const { data, error } = await supabase
        .from('disputes')
        .select('*')
        .eq('status', 'pending');

      if (error) {
        console.error('Error fetching pending disputes:', error);
      }

      if (data) {
        setPendingDisputes(data as Dispute[]);
      }
      setIsLoading(false);
    };

    fetchPendingDisputes();

    const subscription = supabase
      .channel('public:disputes')
      .on('postgres_changes', { event: '*', schema: 'public', table: 'disputes' }, (payload) => {
        console.log('Change received!', payload)
        fetchPendingDisputes();
      })
      .subscribe()

    return () => {
      supabase.removeChannel(subscription)
    }
  }, []);

  return (
    <div>
      <h2>Real-Time Queue</h2>
      {isLoading ? (
        <div>Loading...</div>
      ) : pendingDisputes && pendingDisputes.length === 0 ? (
        <div>No pending disputes.</div>
      ) : (
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Credit Bureau</TableHead>
                <TableHead>Mailing Address</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Created At</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {pendingDisputes && pendingDisputes.map((dispute) => (
                <TableRow key={dispute.id}>
                  <TableCell>{dispute.credit_bureau}</TableCell>
                  <TableCell>
                    <div className="max-h-20 overflow-y-auto">
                      {dispute.mailing_address.split('\n').map((line, i) => (
                        <div key={i}>{line}</div>
                      ))}
                    </div>
                  </TableCell>
                  <TableCell>{getStatusBadge(dispute.status)}</TableCell>
                  <TableCell>{new Date(dispute.created_at).toLocaleDateString()}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  );
};

export default RealTimeQueue;