import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'POST',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

interface EmailPayload {
  type: 'dispute_packet_ready' | 'dispute_sent' | 'welcome'
  to: string
  userName: string
  data?: Record<string, unknown>
}

const buildEmailHtml = (payload: EmailPayload): { subject: string; html: string } => {
  const { userName, type, data } = payload

  switch (type) {
    case 'welcome':
      return {
        subject: 'Welcome to Credit Clarity!',
        html: `
          <div style="font-family:sans-serif;max-width:600px;margin:0 auto;background:#0F1729;color:#CBD5E1;padding:32px;border-radius:12px;">
            <h1 style="color:#D4A853;margin-bottom:8px;">Welcome to Credit Clarity</h1>
            <p>Hi ${userName},</p>
            <p>Your account is ready. Start by uploading your credit report to identify negative items you can dispute.</p>
            <a href="${data?.appUrl ?? 'https://creditclarity.app'}/credit-report-upload"
               style="display:inline-block;background:linear-gradient(135deg,#D4A853,#E8C06A);color:#0A0F1E;font-weight:bold;padding:12px 24px;border-radius:8px;text-decoration:none;margin-top:16px;">
              Upload Credit Report
            </a>
            <p style="margin-top:32px;font-size:12px;color:#4A5568;">Credit Clarity · Not legal advice</p>
          </div>`,
      }

    case 'dispute_packet_ready':
      return {
        subject: 'Your Dispute Packet is Ready',
        html: `
          <div style="font-family:sans-serif;max-width:600px;margin:0 auto;background:#0F1729;color:#CBD5E1;padding:32px;border-radius:12px;">
            <h1 style="color:#D4A853;margin-bottom:8px;">Your Dispute Packet is Ready</h1>
            <p>Hi ${userName},</p>
            <p>Your dispute letters have been generated for <strong style="color:#F0F4FF;">${data?.bureauCount ?? ''} bureau${(data?.bureauCount as number) !== 1 ? 's' : ''}</strong> covering <strong style="color:#F0F4FF;">${data?.itemCount ?? ''} item${(data?.itemCount as number) !== 1 ? 's' : ''}</strong>.</p>
            <p><strong style="color:#F0F4FF;">Next steps:</strong></p>
            <ol style="padding-left:20px;line-height:1.8;">
              <li>Download your dispute packet from the Dispute Wizard</li>
              <li>Print each letter and sign where indicated</li>
              <li>Mail via Certified Mail to each bureau (see cover pages for addresses)</li>
              <li>Keep your tracking numbers — bureaus have 30 days to respond</li>
            </ol>
            <a href="${data?.appUrl ?? 'https://creditclarity.app'}/dispute-wizard"
               style="display:inline-block;background:linear-gradient(135deg,#D4A853,#E8C06A);color:#0A0F1E;font-weight:bold;padding:12px 24px;border-radius:8px;text-decoration:none;margin-top:16px;">
              View Dispute Wizard
            </a>
            <p style="margin-top:32px;font-size:12px;color:#4A5568;">Credit Clarity · Not legal advice</p>
          </div>`,
      }

    case 'dispute_sent':
      return {
        subject: 'Dispute Letter Sent via Mail',
        html: `
          <div style="font-family:sans-serif;max-width:600px;margin:0 auto;background:#0F1729;color:#CBD5E1;padding:32px;border-radius:12px;">
            <h1 style="color:#D4A853;margin-bottom:8px;">Dispute Letter Sent</h1>
            <p>Hi ${userName},</p>
            <p>Your dispute letter to <strong style="color:#F0F4FF;">${data?.bureau}</strong> has been mailed.</p>
            ${data?.trackingNumber ? `<p>Tracking number: <strong style="color:#D4A853;">${data.trackingNumber}</strong></p>` : ''}
            <p>The bureau has 30–45 days to investigate and respond.</p>
            <p style="margin-top:32px;font-size:12px;color:#4A5568;">Credit Clarity · Not legal advice</p>
          </div>`,
      }

    default:
      return { subject: 'Credit Clarity Notification', html: `<p>Hi ${userName},</p>` }
  }
}

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { status: 200, headers: corsHeaders })
  }

  try {
    const authHeader = req.headers.get('Authorization')
    const supabase = createClient(
      Deno.env.get('SUPABASE_URL')!,
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!,
      authHeader ? { global: { headers: { Authorization: authHeader } } } : undefined
    )

    const payload: EmailPayload = await req.json()
    if (!payload.to || !payload.type) {
      return new Response(JSON.stringify({ error: 'Missing to or type' }), {
        status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      })
    }

    const resendKey = Deno.env.get('RESEND_API_KEY')
    if (!resendKey) {
      return new Response(JSON.stringify({ error: 'Email service not configured' }), {
        status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      })
    }

    const { subject, html } = buildEmailHtml(payload)

    const res = await fetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: { Authorization: `Bearer ${resendKey}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({
        from: 'Credit Clarity <noreply@creditclarity.app>',
        to: [payload.to],
        subject,
        html,
      }),
    })

    if (!res.ok) {
      const err = await res.text()
      console.error('[send-email] Resend error:', err)
      return new Response(JSON.stringify({ error: 'Email delivery failed' }), {
        status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      })
    }

    const result = await res.json()
    return new Response(JSON.stringify({ success: true, id: result.id }), {
      status: 200, headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    })
  } catch (err) {
    console.error('[send-email] Error:', err)
    return new Response(JSON.stringify({ error: 'Internal server error' }), {
      status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    })
  }
})
