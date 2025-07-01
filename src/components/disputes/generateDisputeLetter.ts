
import { ParsedTradeline } from "@/utils/tradelineParser";

interface UserInfo {
  firstName: string;
  lastName: string;
  address: string;
  city: string;
  state: string;
  zip: string;
  phoneNumber?: string;
  emailAddress?: string;
}

interface CreditBureau {
  name: string;
  address: string;
  city: string;
  state: string;
  zip: string;
  phoneNumber?: string;
}

export async function generateDisputeLetter(
  userInfo: UserInfo,
  selectedTradelines: ParsedTradeline[],
  creditBureau: CreditBureau
): Promise<string> {
  const currentDate = new Date().toLocaleDateString("en-US", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });

  const disputedItems = selectedTradelines
    .map((t, i) => {
      return `${i + 1}. Creditor Name: ${t.creditor_name}\n   Account Number: ${t.account_number}\n   Reason for Dispute: This item is inaccurate or does not belong to me.`;
    })
    .join("\\n\\n");

  const rawLetter = `
${userInfo.firstName} ${userInfo.lastName}
${userInfo.address}
${userInfo.city}, ${userInfo.state} ${userInfo.zip}
${userInfo.phoneNumber || "[Phone Number]"}
${userInfo.emailAddress || "[Email Address]"}

${currentDate}

Complaint Department
${creditBureau.name}
${creditBureau.address}
${creditBureau.city}, ${creditBureau.state} ${creditBureau.zip}

Re: Dispute of Tradeline Information

Dear ${creditBureau.name},

I am writing to formally dispute the accuracy of the following information in my credit report:

${disputedItems}

Under the Fair Credit Reporting Act (FCRA) Section 611, I am entitled to dispute any information on my credit report that I believe is inaccurate. It is my understanding that the credit reporting agencies are required to conduct a reasonable investigation into the disputed information within 30 days of receiving the dispute.

I respectfully request that you investigate this matter and provide me with a detailed explanation of how this information was verified and found to be accurate. If you find the information to be inaccurate, I request that it be corrected or removed from my credit report in accordance with the FCRA.

Enclosures:
- A copy of my photo ID
- A copy of my SSN card
- A copy of my utility bill

Thank you for your prompt attention to this matter.

Sincerely,

${userInfo.firstName} ${userInfo.lastName}
`.trim();

  return rawLetter;
}
