import { Claude } from "@anthropic-ai/sdk";

export const viteAgent = async (input: string) => {
  const client = new Claude({ apiKey: process.env.VITE_CLAUDE_API_KEY });

  const prompt = `
You are the VITE-CODE-ENFORCER agent.
Your job is to ensure incoming code:

- Uses Vite, NOT Next.js
- Does NOT use Next.js-specific APIs (app router, pages router, getServerSideProps, etc.)
- Uses Vite environment variables: import.meta.env.VITE_*
- Uses react-router instead of next/navigation
- Uses index.html entrypoint logic
- Follows Vite file structure

Input code:
${input}

Return ONLY corrected code.
`;

  const res = await client.messages.create({
    model: "claude-3.5-sonnet",
    max_tokens: 4096,
    messages: [{ role: "user", content: prompt }]
  });

  return res.content[0].text;
};
