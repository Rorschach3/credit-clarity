import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'
import Stripe from 'https://esm.sh/stripe@14?target=deno'

serve(async (req) => {
  const stripeKey = Deno.env.get('STRIPE_SECRET_KEY')!
  const webhookSecret = Deno.env.get('STRIPE_WEBHOOK_SECRET')!
  const stripe = new Stripe(stripeKey, { apiVersion: '2023-10-16' })

  const signature = req.headers.get('stripe-signature')
  if (!signature) {
    return new Response('Missing stripe-signature', { status: 400 })
  }

  const body = await req.text()
  let event: Stripe.Event

  try {
    event = await stripe.webhooks.constructEventAsync(body, signature, webhookSecret)
  } catch (err) {
    console.error('[stripe-webhook] Signature verification failed:', err)
    return new Response('Invalid signature', { status: 400 })
  }

  const supabase = createClient(
    Deno.env.get('SUPABASE_URL')!,
    Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
  )

  try {
    switch (event.type) {
      case 'checkout.session.completed': {
        const session = event.data.object as Stripe.Checkout.Session
        const userId = session.metadata?.user_id ?? session.client_reference_id

        if (!userId) break

        if (session.mode === 'payment') {
          // Credit package purchase — add credits to user_credits
          const credits = parseInt(session.metadata?.credits ?? '0', 10)
          if (credits <= 0) break

          await supabase.rpc('add_credits', {
            p_user_id: userId,
            p_amount: credits,
            p_description: `Credit purchase — ${credits} credits`,
          })

          console.log(`[stripe-webhook] Added ${credits} credits for user ${userId}`)
        } else if (session.mode === 'subscription') {
          // Subscription purchase
          const subscriptionId = session.subscription as string
          if (!subscriptionId) break

          const subscription = await stripe.subscriptions.retrieve(subscriptionId)
          const priceId = subscription.items.data[0]?.price.id ?? ''

          await supabase.from('user_subscriptions').upsert({
            user_id: userId,
            stripe_subscription_id: subscriptionId,
            plan_id: priceId,
            status: subscription.status,
            started_at: new Date(subscription.start_date * 1000).toISOString(),
          }, { onConflict: 'user_id' })

          console.log(`[stripe-webhook] Subscription activated for user ${userId}`)
        }
        break
      }

      case 'customer.subscription.updated': {
        const subscription = event.data.object as Stripe.Subscription
        const userId = subscription.metadata?.user_id

        if (!userId) {
          await supabase.from('user_subscriptions')
            .update({ status: subscription.status, plan_id: subscription.items.data[0]?.price.id ?? '' })
            .eq('stripe_subscription_id', subscription.id)
        } else {
          await supabase.from('user_subscriptions')
            .update({ status: subscription.status, plan_id: subscription.items.data[0]?.price.id ?? '' })
            .eq('user_id', userId)
        }
        break
      }

      case 'customer.subscription.deleted': {
        const subscription = event.data.object as Stripe.Subscription

        await supabase.from('user_subscriptions')
          .update({ status: 'cancelled', ended_at: new Date().toISOString() })
          .eq('stripe_subscription_id', subscription.id)

        console.log(`[stripe-webhook] Subscription cancelled: ${subscription.id}`)
        break
      }

      default:
        console.log(`[stripe-webhook] Unhandled event type: ${event.type}`)
    }
  } catch (err) {
    console.error('[stripe-webhook] Handler error:', err)
    return new Response('Handler error', { status: 500 })
  }

  return new Response(JSON.stringify({ received: true }), {
    status: 200, headers: { 'Content-Type': 'application/json' },
  })
})
