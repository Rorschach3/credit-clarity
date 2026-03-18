import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import "https://deno.land/x/xhr@0.1.0/mod.ts"

serve(async (req) => {
  const { method } = req

  // Handle CORS preflight requests
  if (method === 'OPTIONS') {
    return new Response(null, {
      status: 200,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST',
        'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
      },
    })
  }

  if (method !== 'POST') {
    return new Response(JSON.stringify({ error: 'Method not allowed' }), {
      status: 405,
      headers: { 'Content-Type': 'application/json' },
    })
  }

  try {
    const { 
      personalInfo, 
      selectedTradelines, 
      bureaus,
      letterType = 'basic',
      customInstructions 
    } = await req.json()

    // Validate required fields
    if (!personalInfo || !selectedTradelines || !bureaus) {
      return new Response(
        JSON.stringify({ error: 'Missing required fields: personalInfo, selectedTradelines, bureaus' }),
        { status: 400, headers: { 'Content-Type': 'application/json' } }
      )
    }

    // Get OpenAI API key from environment
    const openaiApiKey = Deno.env.get('OPENAI_API_KEY')
    if (!openaiApiKey) {
      console.error('[generate-dispute-letter] OPENAI_API_KEY is not set in Edge Function secrets')
      return new Response(
        JSON.stringify({ error: 'OpenAI API key not configured. Set OPENAI_API_KEY in Supabase Edge Function secrets.' }),
        { status: 500, headers: { 'Content-Type': 'application/json' } }
      )
    }

    const disputeLetters: Record<string, string> = {}

    // Generate letter for each bureau
    for (const bureau of bureaus) {
      const bureauTradelines = selectedTradelines.filter((t: any) => 
        !t.credit_bureau || t.credit_bureau === bureau || t.credit_bureau === ''
      )

      if (bureauTradelines.length === 0) continue

      const prompt = createDisputeLetterPrompt({
        personalInfo,
        tradelines: bureauTradelines,
        bureau,
        letterType,
        customInstructions
      })

      try {
        const response = await fetch('https://api.openai.com/v1/chat/completions', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${openaiApiKey}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            model: 'gpt-4-turbo-preview',
            messages: [
              {
                role: 'system',
                content: 'You are a professional credit dispute letter writer with expertise in FCRA compliance and consumer rights. Generate formal, legally compliant dispute letters.'
              },
              {
                role: 'user',
                content: prompt
              }
            ],
            max_tokens: 2000,
            temperature: 0.3
          })
        })

        if (!response.ok) {
          const errBody = await response.text().catch(() => '')
          throw new Error(`OpenAI API error ${response.status}: ${errBody}`)
        }

        const data = await response.json()
        const content = data.choices[0]?.message?.content
        if (!content) {
          throw new Error('OpenAI returned empty content')
        }
        disputeLetters[bureau] = content
      } catch (error) {
        console.error(`[generate-dispute-letter] OpenAI call failed for bureau "${bureau}": ${error instanceof Error ? error.message : String(error)}. Using fallback template.`)
        disputeLetters[bureau] = generateFallbackLetter(personalInfo, bureauTradelines, bureau)
      }
    }

    return new Response(
      JSON.stringify({ 
        success: true, 
        letters: disputeLetters,
        generatedAt: new Date().toISOString()
      }),
      {
        status: 200,
        headers: { 
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*'
        }
      }
    )

  } catch (error) {
    const message = error instanceof Error ? error.message : String(error)
    console.error('[generate-dispute-letter] Unhandled error:', message)
    return new Response(
      JSON.stringify({
        error: 'Internal server error',
        details: message
      }),
      {
        status: 500,
        headers: { 
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*'
        }
      }
    )
  }
})

function createDisputeLetterPrompt({ personalInfo, tradelines, bureau, letterType, customInstructions }: any) {
  const now = new Date()
  const day = now.getDate()
  const teen = day % 100
  const suffix =
    teen >= 11 && teen <= 13
      ? 'th'
      : day % 10 === 1
        ? 'st'
        : day % 10 === 2
          ? 'nd'
          : day % 10 === 3
            ? 'rd'
            : 'th'
  const currentDate = `${now.toLocaleDateString('en-US', { month: 'long' })} ${day}${suffix} ${now.getFullYear()}`

  const bureauAddresses = {
    'Experian': `Experian
P.O. Box 4500
Allen, TX 75013`,
    'TransUnion': `TransUnion
P.O. Box 2000
Chester, PA 19016`,
    'Equifax': `Equifax Information Services LLC
P.O. Box 740256
Atlanta, GA 30374`
  }

  const tradelineDescriptions = tradelines.map((t: any) => {
    return `- ${t.creditor_name}
  # ${t.account_number}
  ${t.account_balance || ''}
  ${t.date_opened || ''}
  ${t.account_status || t.dispute_reason || 'Negative information reported in error'}`
  }).join('\n\n')

  return `Generate a professional, FCRA-compliant credit dispute letter with the following details:

SENDER INFORMATION:
Name: ${personalInfo.firstName} ${personalInfo.lastName}
Address: ${personalInfo.address}${personalInfo.address2 ? ', ' + personalInfo.address2 : ''}
City, State ZIP: ${personalInfo.city}, ${personalInfo.state} ${personalInfo.zip}
Phone: ${personalInfo.phone || '[Phone Number]'}
SSN: XXX-XX-${personalInfo.lastFourSSN || 'XXXX'}

RECIPIENT:
${bureauAddresses[bureau as keyof typeof bureauAddresses]}

DATE: ${currentDate}

DISPUTED ITEMS:
${tradelineDescriptions}

REQUIREMENTS:
- Match a plain one-page consumer dispute letter style, not a formal legal memo
- Start with the bureau mailing address, then the date, then "Dear Sir or Madam,"
- Use two short body paragraphs in simple language
- Ask for proof of the investigation results within 30 days
- State that the items should be deleted if they cannot be verified
- After the body, list the disputed items as a simple stacked list with creditor name and supporting details, not a table
- End with "Sincerely," followed by the consumer's name, address, and masked SSN in the format "SS: XXX-XX-1234"
- Do not include a "Re:" line
- Do not include an enclosures section
- Keep the tone direct and professional, similar to a traditional mailed consumer dispute letter
${customInstructions ? `- Custom instructions: ${customInstructions}` : ''}

Generate only the letter content, properly formatted for printing and mailing.`
}

function generateFallbackLetter(personalInfo: any, tradelines: any[], bureau: string): string {
  const now = new Date()
  const day = now.getDate()
  const teen = day % 100
  const suffix =
    teen >= 11 && teen <= 13
      ? 'th'
      : day % 10 === 1
        ? 'st'
        : day % 10 === 2
          ? 'nd'
          : day % 10 === 3
            ? 'rd'
            : 'th'
  const currentDate = `${now.toLocaleDateString('en-US', { month: 'long' })} ${day}${suffix} ${now.getFullYear()}`

  const bureauAddresses = {
    'Experian': `Experian
P.O. Box 4500
Allen, TX 75013`,
    'TransUnion': `TransUnion
P.O. Box 2000
Chester, PA 19016`,
    'Equifax': `Equifax Information Services LLC
P.O. Box 740256
Atlanta, GA 30374`
  }

  const disputedItems = tradelines.map((t: any) => {
    const lines = [`- ${t.creditor_name}`]
    if (t.account_number) lines.push(`  # ${t.account_number}`)
    if (t.account_balance) lines.push(`  ${t.account_balance}`)
    if (t.date_opened) lines.push(`  ${t.date_opened}`)
    if (t.account_status || t.dispute_reason) lines.push(`  ${t.account_status || t.dispute_reason}`)
    return lines.join('\n')
  }).join('\n\n')

  return `${bureauAddresses[bureau as keyof typeof bureauAddresses] ?? `${bureau} Consumer Dispute Department`}

${currentDate}

Dear Sir or Madam,

I found incorrect information being reported on my credit report. I need these accounts verified for accuracy. Please send all proof of the investigation results to me within 30 days. If no proof is sent to me, please delete these items from my credit report.

The items listed below should be corrected or removed if they cannot be fully verified.

${disputedItems}

Sincerely,

${personalInfo.firstName} ${personalInfo.lastName}
${personalInfo.address}${personalInfo.address2 ? '\n' + personalInfo.address2 : ''}
${personalInfo.city} ${personalInfo.state} ${personalInfo.zip}
SS: XXX-XX-${personalInfo.lastFourSSN || 'XXXX'}`
}
