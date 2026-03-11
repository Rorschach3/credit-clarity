import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'
import Stripe from 'https://esm.sh/stripe@14?target=deno'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'POST',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { status: 200, headers: corsHeaders })
  }

  try {
    const authHeader = req.headers.get('Authorization')
    if (!authHeader) {
      return new Response(JSON.stringify({ error: 'Missing authorization header' }), {
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

    const { priceId, mode, credits } = await req.json()
    if (!priceId || !mode) {
      return new Response(JSON.stringify({ error: 'Missing priceId or mode' }), {
        status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      })
    }

    const stripeKey = Deno.env.get('STRIPE_SECRET_KEY')
    if (!stripeKey) {
      return new Response(JSON.stringify({ error: 'Stripe not configured' }), {
        status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      })
    }

    const stripe = new Stripe(stripeKey, { apiVersion: '2023-10-16' })
    const origin = req.headers.get('origin') ?? 'https://localhost:5173'

    const sessionParams: Stripe.Checkout.SessionCreateParams = {
      mode: mode as 'payment' | 'subscription',
      payment_method_types: ['card'],
      line_items: [{ price: priceId, quantity: 1 }],
      client_reference_id: user.id,
      customer_email: user.email,
      metadata: { user_id: user.id, ...(credits ? { credits: String(credits) } : {}) },
    }

    if (mode === 'payment') {
      sessionParams.success_url = `${origin}/dispute-history?credits=purchased`
      sessionParams.cancel_url = `${origin}/dispute-history`
    } else {
      sessionParams.success_url = `${origin}/dashboard?checkout=success`
      sessionParams.cancel_url = `${origin}/pricing?checkout=cancelled`
    }

    const session = await stripe.checkout.sessions.create(sessionParams)

    return new Response(JSON.stringify({ url: session.url }), {
      status: 200, headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    })
  } catch (err) {
    console.error('[create-checkout] Error:', err)
    return new Response(JSON.stringify({ error: 'Internal server error' }), {
      status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    })
  }
})
