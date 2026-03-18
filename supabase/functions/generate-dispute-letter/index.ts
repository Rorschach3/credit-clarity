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
    const reportedStatus = t.account_status || 'Unknown'
    const reason = t.dispute_reason
      || `The current status of this account (listed as "${reportedStatus}") is inaccurate. Alternatively, if this account is being reported past the allowable reporting timeframe, it is obsolete and must be removed.`

    return `Creditor Name: ${t.creditor_name}
Account #: ${t.account_number}
Reported Status: ${reportedStatus}
${t.account_balance ? `Balance: ${t.account_balance}\n` : ''}${t.date_opened ? `Date Opened: ${t.date_opened}\n` : ''}Reason for Dispute: ${reason}`
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
- Use the following order:
  1. Consumer name and mailing address
  2. Date
  3. Bureau mailing address
  4. "RE: Dispute of Inaccurate Information"
  5. "File/Report Number: [Insert Report Number Here]" unless a report number was provided
  6. "Social Security Number: XXX-XX-1234"
  7. "To Whom It May Concern:"
- Cite the Fair Credit Reporting Act as "15 U.S.C. § 1681i"
- State that the bureau must investigate, verify with the furnisher, and provide the method of verification
- State that unverifiable items must be deleted within the 30-day timeframe
- For each disputed tradeline, use labeled lines exactly like:
  "Creditor Name:"
  "Account #:"
  "Reported Status:"
  optional "Balance:" and "Date Opened:"
  "Reason for Dispute:"
- The reason for dispute must be specific, not generic
- End with "Sincerely," then the consumer name
- Include an "Enclosures:" section listing the highlighted credit report, government ID, and proof of address
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
    const reportedStatus = t.account_status || 'Unknown'
    const lines = [
      `Creditor Name: ${t.creditor_name}`,
      `Account #: ${t.account_number}`,
      `Reported Status: ${reportedStatus}`,
    ]
    if (t.account_balance) lines.push(`Balance: ${t.account_balance}`)
    if (t.date_opened) lines.push(`Date Opened: ${t.date_opened}`)
    lines.push(`Reason for Dispute: ${t.dispute_reason || `The current status of this account (listed as "${reportedStatus}") is inaccurate. Alternatively, if this account is being reported past the allowable reporting timeframe, it is obsolete and must be removed.`}`)
    return lines.join('\n')
  }).join('\n\n')

  return `${personalInfo.firstName} ${personalInfo.lastName}
${personalInfo.address}${personalInfo.address2 ? '\n' + personalInfo.address2 : ''}
${personalInfo.city}, ${personalInfo.state} ${personalInfo.zip}

${currentDate}

${bureauAddresses[bureau as keyof typeof bureauAddresses] ?? `${bureau} Consumer Dispute Department`}

RE: Dispute of Inaccurate Information
File/Report Number: [Insert Report Number Here]
Social Security Number: XXX-XX-${personalInfo.lastFourSSN || 'XXXX'}

To Whom It May Concern:

I am writing to dispute the following accounts that are reporting inaccurately on my credit report. This information is a serious error and I request that it be investigated and removed immediately pursuant to my rights under the Fair Credit Reporting Act (15 U.S.C. § 1681i).

The following accounts contain incorrect information and/or are obsolete:

${disputedItems}

Please investigate this matter thoroughly. I request that you verify the accuracy of each item with the furnisher of the information and send me the results of your investigation, including the method of verification, to the address above.

If any item cannot be verified within the 30-day timeframe required by law, I expect it to be permanently deleted from my credit file.

Sincerely,

${personalInfo.firstName} ${personalInfo.lastName}

Enclosures:
- Copy of credit report (highlighted)
- Copy of government ID
- Copy of proof of address`
}
