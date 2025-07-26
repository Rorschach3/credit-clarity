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
      return new Response(
        JSON.stringify({ error: 'OpenAI API key not configured' }),
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
          throw new Error(`OpenAI API error: ${response.status}`)
        }

        const data = await response.json()
        disputeLetters[bureau] = data.choices[0]?.message?.content || ''
      } catch (error) {
        console.error(`Error generating letter for ${bureau}:`, error)
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
    console.error('Error in generate-dispute-letter function:', error)
    return new Response(
      JSON.stringify({ 
        error: 'Internal server error',
        details: error.message 
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
  const currentDate = new Date().toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })

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

  const tradelineDescriptions = tradelines.map((t: any, index: number) => {
    return `${index + 1}. Creditor: ${t.creditor_name}
   Account Number: ${t.account_number}
   Current Status: ${t.account_status || 'Unknown'}
   Reason for Dispute: This information is inaccurate/unverifiable${t.dispute_reason ? ` - ${t.dispute_reason}` : ''}`
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
- Use professional business letter format
- Reference Fair Credit Reporting Act (FCRA) Section 611
- Request investigation within 30 days as required by law
- Include standard dispute language about accuracy verification
- Mention enclosures (copy of ID, SSN card, utility bill)
- Request removal if items cannot be verified
- Professional but assertive tone
- Include signature line
${customInstructions ? `- Custom instructions: ${customInstructions}` : ''}

Generate only the letter content, properly formatted for printing and mailing.`
}

function generateFallbackLetter(personalInfo: any, tradelines: any[], bureau: string): string {
  const currentDate = new Date().toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })

  const disputedItems = tradelines.map((t, index) => {
    return `${index + 1}. Creditor Name: ${t.creditor_name}
   Account Number: ${t.account_number}
   Reason for Dispute: This information is inaccurate and should be removed from my credit report.`
  }).join('\n\n')

  return `${personalInfo.firstName} ${personalInfo.lastName}
${personalInfo.address}${personalInfo.address2 ? '\n' + personalInfo.address2 : ''}
${personalInfo.city}, ${personalInfo.state} ${personalInfo.zip}
${personalInfo.phone || '[Phone Number]'}

${currentDate}

${bureau} Consumer Dispute Department
[Address will be inserted based on bureau]

Re: Dispute of Credit Report Information

Dear Sir or Madam:

I am writing to dispute the following information in my credit report. I have circled the items I dispute on the attached copy of the report I received.

The following items are inaccurate or incomplete:

${disputedItems}

Under the Fair Credit Reporting Act, I have the right to request that you verify the accuracy of this information. I am requesting that the item be removed or corrected. Enclosed are copies of documents supporting my position. Please investigate this matter and correct the disputed item as soon as possible.

Sincerely,

${personalInfo.firstName} ${personalInfo.lastName}

Enclosures:
- Copy of photo identification
- Copy of Social Security card  
- Copy of utility bill or bank statement`
}