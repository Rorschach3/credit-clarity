import { supabase } from "../../supabase/client";
import { Account, AccountSchema, DisputeAnalysis, DisputeAnalysisSchema, GeneratedLetter, GeneratedLetterSchema, UserData } from "@/schemas/ai";
import { fetchOpenAIChat } from "../utils/openaiClient";

/**
 * Save an array of tradeline accounts to the database for a given user.
 * @param tradelines Array of Account objects to save.
 * @param userId Supabase user ID to associate with these tradelines.
 * @returns The inserted records data from Supabase.
 * @throws Will throw if a database error occurs.
 */
export async function saveTradelines(tradelines: Account[], userId: string) {
  // Prepare data with user reference
  const rows = tradelines.map(t => ({
    ...t,
    user_id: userId   // assuming the database uses user_id as foreign key
  }));
  const { data, error } = await supabase.from("tradelines").insert(rows);
  if (error) {
    // Supabase returns a typed error; throw it directly (avoid redundant wrapping)
    throw error;
  }
  return data;
}

/**
 * Analyze extracted credit report text using an AI model to identify accounts and negative items.
 * @param extractedText The full text extracted from a credit report (e.g. via OCR).
 * @returns A DisputeAnalysis object containing parsed accounts and a summary of findings.
 * @throws Will throw an error if the AI response is invalid or the OpenAI API call fails.
 */
export async function analyzeDisputeText(extractedText: string): Promise<DisputeAnalysis> {
  // Compose messages for the OpenAI chat completion (system instruction + user prompt)
  const messages = [
    {
      role: "system",
      content: 
        "You are a financial assistant that analyzes credit report text and extracts tradeline information. " +
        "Identify all accounts (tradelines) in the provided text, mark whether each is negative, and if negative provide a brief reason. " +
        "Also provide a summary of the negative items. Respond in JSON format with keys 'accounts' (array of accounts with fields: creditorName, accountNumber, accountStatus, accountBalance, dateOpened, isNegative, negativeReason) and 'summary' (string)."
    },
    {
      role: "user",
      content: extractedText
    }
  ];

  // Call OpenAI API with the messages, expecting a DisputeAnalysis JSON structure in response
  const analysis: DisputeAnalysis = await fetchOpenAIChat(DisputeAnalysisSchema, messages);
  return analysis;
}

/**
 * Generate a formal dispute letter for the given accounts and user data using an AI model.
 * @param accounts List of accounts to dispute (typically negative accounts selected by the user).
 * @param userData The user's personal data (name, address) to include in the letter.
 * @returns A GeneratedLetter object containing the full dispute letter text.
 * @throws Will throw an error if the AI response is invalid or the OpenAI API call fails.
 */
export async function generateDisputeLetter(accounts: Account[], userData: UserData): Promise<GeneratedLetter> {
  // Prepare the content describing user info and disputed accounts for the prompt
  const userInfo = `${userData.name}\n${userData.address}`;
  const accountsListText = accounts.map((acc, index) => {
    const reason = acc.negativeReason || "This item is inaccurate or does not belong to me.";
    return `${index + 1}. Creditor: ${acc.creditorName}, Account Number: ${acc.accountNumber}, Reason: ${reason}`;
  }).join("\n");

  const messages = [
    {
      role: "system",
      content: 
        "You are an assistant that drafts formal credit dispute letters. " +
        "Using the provided user information and list of disputed accounts, write a professional dispute letter. " +
        "The letter should include the user's name and address at the top, a greeting, a reference to the Fair Credit Reporting Act (FCRA) Section 611, a list of disputed items with their creditor names, account numbers, and dispute reasons, a request for investigation within 30 days, and the user's full name. " +
        "Respond ONLY with a JSON object containing a single key 'letter' and the full letter text as its value."
    },
    {
      role: "user",
      content: 
        `User Information:\n${userInfo}\n\nDisputed Accounts:\n${accountsListText}`
    }
  ];

  // Call OpenAI API with the messages, expecting a GeneratedLetter JSON structure in response
  const letter: GeneratedLetter = await fetchOpenAIChat(GeneratedLetterSchema, messages);
  return letter;
}
