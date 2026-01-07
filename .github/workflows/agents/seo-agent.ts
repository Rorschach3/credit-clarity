import { Claude } from "@anthropic-ai/sdk";

export const seoAgent = async (input: string) => {
  const client = new Claude({ apiKey: process.env.VITE_CLAUDE_API_KEY });

  const prompt = `
You are the SEO SPECIALIST agent for Peptide Hub.

Current Status:
- Sitemap: 286 URLs (76 peptides, 30 blogs, 50 research, 20 protocols, 50 videos)
- Auto-generates: npm run seo:sitemap
- Location: frontend/public/sitemap.xml

Commands:
1. Generate: cd frontend && npm run seo:sitemap
2. Check: curl https://www.professorpeptides.org/sitemap.xml
3. Count: grep -c "<url>" frontend/public/sitemap.xml

Task: ${input}

Provide specific SEO recommendations.
`;

  const res = await client.messages.create({
    model: "claude-3-5-sonnet",
    max_tokens: 4096,
    messages: [{ role: "user", content: prompt }]
  });

  return res.content[0].text;
};

export default seoAgent;
