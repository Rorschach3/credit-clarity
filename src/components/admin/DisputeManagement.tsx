
import { useState, useEffect } from 'react'
import { differenceInCalendarDays } from 'date-fns'
import { useToast } from "@/hooks/use-toast"
import { supabase } from "@/integrations/supabase/client"
import type { Tables } from "@/integrations/supabase/types";
import useActivityMonitoring from "@/hooks/use-activity-monitoring";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Printer, Loader2, FileText, TruckIcon } from "lucide-react"
import RealTimeQueue from "./RealTimeQueue"

interface DisputeManagementProps {
  isLoading: boolean
  disputes: Tables<'disputes'>[]
  fetchDisputes: () => Promise<void>
  setDisputes: React.Dispatch<React.SetStateAction<Tables<'disputes'>[]>>
}

export function DisputeManagement({ isLoading, disputes, fetchDisputes }: DisputeManagementProps) {
  const { toast } = useToast()
  const [processingDisputes, setProcessingDisputes] = useState<{ [key: string]: boolean }>({})
  useActivityMonitoring("Viewed Dispute Management")

  const getDeadlineDate = (createdAt: string) => {
    const date = new Date(createdAt)
    date.setDate(date.getDate() + 30) // 30 days from creation
    return date
  }

  async function generateShippingLabel(dispute: Tables<'disputes'>) {
    try {
      setProcessingDisputes(prev => ({ ...prev, [dispute.id]: true }))
      console.log("Generating shipping label for dispute:", dispute)

      if (!dispute.mailing_address) {
        throw new Error("Dispute has no mailing address")
      }

      const addressLines = dispute.mailing_address.split('\n')
      const cityStateZip = addressLines.length > 1 ? addressLines[1].split(',') : ['', '']
      const city = cityStateZip[0].trim()
      const stateZip = cityStateZip[1].trim().split(' ')
      const state = stateZip[0]
      const zip = stateZip.length > 1 ? stateZip[1] : ''

      const response = await supabase.functions.invoke('generate-shipping-label', {
        body: {
          disputeId: dispute.id,
          toAddress: {
            name: dispute.credit_report_id, // Using credit_report_id as name for now
            street1: addressLines[0],
            city: city,
            state: state,
            zip: zip,
            country: 'US'
          }
        }
      })

      if (response.error) {
        console.error("Error from generate-shipping-label function:", response.error)
        throw new Error(response.error.message)
      }

      const { error: updateError } = await supabase
        .from('disputes')
        .update({
          status: 'label_generated'
        })
        .eq('id', dispute.id)

      if (updateError) {
        console.error("Error updating dispute with shipping info:", updateError)
        throw updateError
      }

      toast({
        title: "Success",
        description: "Shipping label generated successfully",
      })

      fetchDisputes()
    } catch (error: unknown) {
      if (error instanceof Error) {
        console.error("Error in generateShippingLabel:", error)
        toast({
          title: "Error",
          description: error.message || "Failed to generate shipping label",
          variant: "destructive",
        })
      }
    } finally {
      setProcessingDisputes(prev => ({ ...prev, [dispute.id]: false }))
    }
  }

  async function markDisputeAsSent(dispute: Tables<'disputes'>) {
    try {
      setProcessingDisputes(prev => ({ ...prev, [dispute.id]: true }))

      const { error } = await supabase
        .from('disputes')
        .update({
          status: 'sent'
        })
        .eq('id', dispute.id)

      if (error) {
        console.error("Error updating dispute status:", error)
        throw error
      }

      toast({
        title: "Success",
        description: "Dispute marked as sent",
      })

      fetchDisputes()
    } catch (error: unknown) {
      if (error instanceof Error) {
        console.error("Error in markDisputeAsSent:", error)
        toast({
          title: "Error",
          description: `Failed to update dispute status: ${error.message}`,
          variant: "destructive",
        })
      }
    } finally {
      setProcessingDisputes(prev => ({ ...prev, [dispute.id]: false }))
    }
  }

  const [escalationThreshold] = useState(35) // Escalate if no response in 35 days

  useEffect(() => {
    const checkDeadlines = async () => {
      const nearingDeadline = disputes.filter(dispute =>
        dispute.created_at && differenceInCalendarDays(new Date(), new Date(dispute.created_at)) >= 25
      )
      
      if (nearingDeadline.length > 0) {
        console.log(`${nearingDeadline.length} disputes nearing deadline`)
      }
    }
    
    checkDeadlines()
    const interval = setInterval(checkDeadlines, 3600000) // Check hourly
    return () => clearInterval(interval)
  }, [disputes])

  return (
    <Card>
      <CardHeader>
        <CardTitle>Dispute Management</CardTitle>
        <CardDescription className="flex gap-2">
          <Badge variant="outline" className="border-blue-200 text-blue-600">
            FCRA §611 Compliance
          </Badge>
          View and manage customer dispute letters and shipments
        </CardDescription>
      </CardHeader>
      <CardContent>
        <RealTimeQueue />
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Credit Report ID</TableHead>
                <TableHead>Created At</TableHead>
                <TableHead>Deadline</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Content Preview</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={6} className="text-center py-8">
                    <div className="flex items-center justify-center">
                      <Loader2 className="h-6 w-6 animate-spin mr-2" />
                      Loading disputes...
                    </div>
                  </TableCell>
                </TableRow>
              ) : disputes.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} className="text-center py-8">
                    No disputes found.
                    <div className="mt-2 text-sm text-muted-foreground">
                      User-generated disputes will appear here.
                    </div>
                  </TableCell>
                </TableRow>
              ) : (
                disputes.map((dispute) => {
                  const createdDate = new Date(dispute.created_at || '')
                  const deadlineDate = getDeadlineDate(dispute.created_at || '')
                  
                  return (
                    <TableRow key={dispute.id}>
                      <TableCell className="font-medium">
                        {dispute.credit_report_id}
                      </TableCell>
                      <TableCell>
                        {createdDate.toLocaleDateString()}
                      </TableCell>
                      <TableCell className={
                        differenceInCalendarDays(new Date(), createdDate) > 25
                          ? 'text-red-600 font-medium'
                          : ''
                      }>
                        {deadlineDate.toLocaleDateString()}
                      </TableCell>
                      <TableCell>
                        <Badge variant={
                          dispute.status === 'escalated' ? 'destructive' : 'outline'
                        }>
                          {dispute.status}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {dispute.mailing_address ? dispute.mailing_address.substring(0, 50) + '...' : 'No content'}
                      </TableCell>
                      <TableCell>
                        {dispute.status === 'pending' ? (
                          <Button
                            onClick={() => generateShippingLabel(dispute)}
                            size="sm"
                            className="flex items-center gap-2"
                            disabled={processingDisputes[dispute.id]}
                          >
                            {processingDisputes[dispute.id] ? (
                              <Loader2 className="h-4 w-4 animate-spin" />
                            ) : (
                              <Printer className="h-4 w-4" />
                            )}
                            Generate Label
                          </Button>
                        ) : dispute.status === 'label_generated' ? (
                          <Button
                            onClick={() => markDisputeAsSent(dispute)}
                            size="sm"
                            variant="outline"
                            disabled={processingDisputes[dispute.id]}
                          >
                            {processingDisputes[dispute.id] ? (
                              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                            ) : (
                              <TruckIcon className="h-4 w-4 mr-2" />
                            )}
                            Mark as Sent
                          </Button>
                        ) : (
                          <div className="text-sm text-muted-foreground">
                            {dispute.status}
                          </div>
                        )}
                      </TableCell>
                    </TableRow>
                  )
                })
              )}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  )
}
