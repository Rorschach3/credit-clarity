import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'POST',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

const BUREAU_ADDRESSES: Record<string, { name: string; address_line1: string; address_city: string; address_state: string; address_zip: string; address_country: string }> = {
  TransUnion: {
    name: 'TransUnion LLC Consumer Dispute Center',
    address_line1: 'P.O. Box 2000',
    address_city: 'Chester',
    address_state: 'PA',
    address_zip: '19016',
    address_country: 'US',
  },
  Experian: {
    name: 'Experian',
    address_line1: 'P.O. Box 4500',
    address_city: 'Allen',
    address_state: 'TX',
    address_zip: '75013',
    address_country: 'US',
  },
  Equifax: {
    name: 'Equifax Information Services LLC',
    address_line1: 'P.O. Box 740256',
    address_city: 'Atlanta',
    address_state: 'GA',
    address_zip: '30374',
    address_country: 'US',
  },
}

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { status: 200, headers: corsHeaders })
  }

  try {
    const authHeader = req.headers.get('Authorization')
    if (!authHeader) {
      return new Response(JSON.stringify({ error: 'Unauthorized' }), {
        status: 401, headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      })
    }

    const supabase = createClient(
      Deno.env.get('SUPABASE_URL')!,
      Deno.env.get('SUPABASE_ANON_KEY')!,
      { global: { headers: { Authorization: authHeader } } }
    )

    const { data: { user }, error: authError } = await supabase.auth.getUser()
    if (authError || !user) {
      return new Response(JSON.stringify({ error: 'Unauthorized' }), {
        status: 401, headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      })
    }

    const { bureau, letterContent, fromAddress } = await req.json()
    // fromAddress: { name, address_line1, address_city, address_state, address_zip }

    if (!bureau || !letterContent || !fromAddress) {
      return new Response(JSON.stringify({ error: 'Missing bureau, letterContent, or fromAddress' }), {
        status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      })
    }

    const toAddress = BUREAU_ADDRESSES[bureau as keyof typeof BUREAU_ADDRESSES]
    if (!toAddress) {
      return new Response(JSON.stringify({ error: `Unknown bureau: ${bureau}` }), {
        status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      })
    }

    const lobKey = Deno.env.get('LOB_API_KEY')
    if (!lobKey) {
      return new Response(JSON.stringify({ error: 'Mailing service not configured' }), {
        status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      })
    }

    const auth = btoa(`${lobKey}:`)

    // Create the letter via Lob API
    const lobRes = await fetch('https://api.lob.com/v1/letters', {
      method: 'POST',
      headers: {
        Authorization: `Basic ${auth}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        description: `Credit Dispute Letter - ${bureau}`,
        to: {
          name: toAddress.name,
          address_line1: toAddress.address_line1,
          address_city: toAddress.address_city,
          address_state: toAddress.address_state,
          address_zip: toAddress.address_zip,
          address_country: toAddress.address_country,
        },
        from: {
          name: fromAddress.name,
          address_line1: fromAddress.address_line1,
          address_city: fromAddress.address_city,
          address_state: fromAddress.address_state,
          address_zip: fromAddress.address_zip,
          address_country: 'US',
        },
        file: `<html><body style="font-family:Arial,sans-serif;font-size:12pt;margin:40px;"><pre style="white-space:pre-wrap;font-family:Arial,sans-serif;">${letterContent.replace(/</g, '&lt;').replace(/>/g, '&gt;')}</pre></body></html>`,
        color: false,
        double_sided: false,
        address_placement: 'top_first_page',
        return_envelope: false,
        perforated_page: null,
      }),
    })

    if (!lobRes.ok) {
      const err = await lobRes.json()
      console.error('[mail-letter] Lob error:', err)
      return new Response(JSON.stringify({ error: err.error?.message ?? 'Mailing failed' }), {
        status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      })
    }

    const letter = await lobRes.json()

    // Record the mailing in the disputes table
    await supabase
      .from('disputes')
      .update({ lob_id: letter.id, status: 'sent' })
      .eq('user_id', user.id)
      .eq('bureau', bureau)
      .is('lob_id', null)

    return new Response(
      JSON.stringify({
        success: true,
        letterId: letter.id,
        expectedDelivery: letter.expected_delivery_date,
        trackingNumber: letter.tracking_number ?? null,
      }),
      { status: 200, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  } catch (err) {
    console.error('[mail-letter] Error:', err)
    return new Response(JSON.stringify({ error: 'Internal server error' }), {
      status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    })
  }
})
