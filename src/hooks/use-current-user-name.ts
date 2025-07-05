import { supabase } from '@/integrations/supabase/client';
import { useEffect, useState } from 'react'
import type { Session } from '@supabase/supabase-js'

export const useCurrentUserName = () => {
  const [name, setName] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const extractNameFromSession = (session: Session | null) => {
      if (!session?.user) {
        setName(null)
        return
      }

      const { user } = session
      const metadata = user.user_metadata || {}
      
      // Try different metadata fields that might contain the name
      const fullName = metadata.full_name || metadata.name
      const firstName = metadata.first_name || metadata.given_name
      const lastName = metadata.last_name || metadata.family_name
      
      const displayName = fullName || 
                         (firstName && lastName ? `${firstName} ${lastName}` : '') ||
                         firstName || 
                         user.email?.split('@')[0] || // fallback to email username
                         'User'

      setName(displayName)
    }

    const getInitialSession = async () => {
      try {
        const { data: { session }, error } = await supabase.auth.getSession()
        
        if (error) {
          console.error('Error fetching session:', error)
          setName(null)
        } else {
          extractNameFromSession(session)
        }
      } catch (error) {
        console.error('Error in getInitialSession:', error)
        setName(null)
      } finally {
        setLoading(false)
      }
    }

    // Get initial session
    getInitialSession()

    // Listen for auth changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      (event, session) => {
        console.log('Auth state changed:', event, session?.user?.email)
        extractNameFromSession(session)
        setLoading(false)
      }
    )

    return () => {
      subscription.unsubscribe()
    }
  }, [])

  return { name: name || '?', loading }
}