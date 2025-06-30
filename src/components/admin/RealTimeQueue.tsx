
import { useEffect, useState } from 'react'
import { supabase } from '@/integrations/supabase/client'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Clock, FileText, Send } from 'lucide-react'
import type { Tables } from '@/integrations/supabase/types'
import { useToast } from '@/hooks/use-toast'

interface QueuedDispute extends Tables<'disputes'> {
  created_at_date: Date
}

export default function RealTimeQueue() {
  const [queuedDisputes, setQueuedDisputes] = useState<QueuedDispute[]>([])
  const [loading, setLoading] = useState(true)
  const { toast } = useToast()

  useEffect(() => {
    fetchQueuedDisputes()
    
    // Set up real-time subscription
    const subscription = supabase
      .channel('disputes_queue')
      .on('postgres_changes', {
        event: '*',
        schema: 'public',
        table: 'disputes'
      }, () => {
        fetchQueuedDisputes()
      })
      .subscribe()

    return () => {
      subscription.unsubscribe()
    }
  }, [])

  const fetchQueuedDisputes = async () => {
    try {
      const { data, error } = await supabase
        .from('disputes')
        .select('*')
        .in('status', ['pending', 'queued'])
        .order('created_at', { ascending: true })

      if (error) throw error

      // Convert string dates to Date objects
      const disputesWithDates: QueuedDispute[] = (data || []).map(dispute => ({
        ...dispute,
        created_at_date: new Date(dispute.created_at || '')
      }))

      setQueuedDisputes(disputesWithDates)
    } catch (error) {
      console.error('Error fetching queued disputes:', error)
      toast({
        title: "Error",
        description: "Failed to fetch queued disputes",
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }

  const processDispute = async (disputeId: string) => {
    try {
      const { error } = await supabase
        .from('disputes')
        .update({ status: 'processing' })
        .eq('id', disputeId)

      if (error) throw error

      toast({
        title: "Success",
        description: "Dispute moved to processing",
      })

      fetchQueuedDisputes()
    } catch (error) {
      console.error('Error processing dispute:', error)
      toast({
        title: "Error",
        description: "Failed to process dispute",
        variant: "destructive",
      })
    }
  }

  if (loading) {
    return (
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="h-5 w-5" />
            Real-Time Queue
          </CardTitle>
          <CardDescription>Loading queue...</CardDescription>
        </CardHeader>
      </Card>
    )
  }

  return (
    <Card className="mb-6">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Clock className="h-5 w-5" />
          Real-Time Queue
        </CardTitle>
        <CardDescription>
          Disputes waiting to be processed ({queuedDisputes.length} items)
        </CardDescription>
      </CardHeader>
      <CardContent>
        {queuedDisputes.length === 0 ? (
          <p className="text-muted-foreground text-center py-4">
            No disputes in queue
          </p>
        ) : (
          <div className="space-y-3">
            {queuedDisputes.slice(0, 5).map((dispute) => (
              <div key={dispute.id} className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
                <div className="flex items-center gap-3">
                  <FileText className="h-4 w-4 text-muted-foreground" />
                  <div>
                    <p className="font-medium text-sm">
                      Report ID: {dispute.credit_report_id}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      Queued: {dispute.created_at_date.toLocaleString()}
                    </p>
                    {dispute.mailing_address && (
                      <p className="text-xs text-muted-foreground">
                        Address: {dispute.mailing_address.substring(0, 30)}...
                      </p>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant="secondary">{dispute.status}</Badge>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => processDispute(dispute.id)}
                  >
                    <Send className="h-3 w-3 mr-1" />
                    Process
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
