
import { useState, useEffect } from 'react'
import { supabase } from '@/integrations/supabase/client'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Truck, Package, AlertCircle } from 'lucide-react'
import { useToast } from '@/hooks/use-toast'

export default function PostageManagement() {
  const [letters, setLetters] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const { toast } = useToast()

  useEffect(() => {
    fetchLetters()
  }, [])

  const fetchLetters = async () => {
    try {
      const { data, error } = await supabase
        .from('letters')
        .select('*')
        .order('created_at', { ascending: false })

      if (error) throw error
      setLetters(data || [])
    } catch (error) {
      console.error('Error fetching letters:', error)
      toast({
        title: "Error",
        description: "Failed to fetch letters",
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }

  const updateLetterStatus = async (letterId: string, newStatus: string) => {
    try {
      const { error } = await supabase
        .from('letters')
        .update({ status: newStatus })
        .eq('id', letterId)

      if (error) throw error

      toast({
        title: "Success",
        description: `Letter status updated to ${newStatus}`,
      })

      fetchLetters()
    } catch (error) {
      console.error('Error updating letter status:', error)
      toast({
        title: "Error",
        description: "Failed to update letter status",
        variant: "destructive",
      })
    }
  }

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>PostageManagement</CardTitle>
          <CardDescription>Loading...</CardDescription>
        </CardHeader>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Package className="h-5 w-5" />
          Postage Management
        </CardTitle>
        <CardDescription>
          Manage letter delivery and tracking
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {letters.length === 0 ? (
            <p className="text-muted-foreground text-center py-8">
              No letters found
            </p>
          ) : (
            letters.map((letter) => (
              <div key={letter.id} className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex items-center gap-3">
                  <div className="flex items-center gap-2">
                    {letter.status === 'delivered' ? (
                      <Truck className="h-4 w-4 text-green-600" />
                    ) : letter.status === 'error' ? (
                      <AlertCircle className="h-4 w-4 text-red-600" />
                    ) : (
                      <Package className="h-4 w-4 text-blue-600" />
                    )}
                  </div>
                  <div>
                    <p className="font-medium">{letter.to_name}</p>
                    <p className="text-sm text-muted-foreground">
                      {letter.to_address}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      Created: {new Date(letter.created_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant={
                    letter.status === 'delivered' ? 'default' :
                    letter.status === 'error' ? 'destructive' : 'secondary'
                  }>
                    {letter.status}
                  </Badge>
                  {letter.status === 'pending' && (
                    <Button
                      size="sm"
                      onClick={() => updateLetterStatus(letter.id, 'sent')}
                    >
                      Mark as Sent
                    </Button>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      </CardContent>
    </Card>
  )
}
