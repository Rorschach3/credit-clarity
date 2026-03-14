import React from "react";
import { Accordion, AccordionItem, AccordionTrigger, AccordionContent } from "@/components/ui/accordion";
import { FileText, Brain, Rocket } from "lucide-react";
import { Helmet } from "react-helmet-async";

export default function FaqPage() {
  const faqJsonLd = {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: [
      {
        "@type": "Question",
        name: "Why are dispute letters the foundation of credit repair?",
        acceptedAnswer: {
          "@type": "Answer",
          text:
            "Dispute letters invoke your rights under the FCRA and require bureaus and furnishers to investigate and verify reported information within the legal timeframe.",
        },
      },
      {
        "@type": "Question",
        name: "How does sending multiple dispute letters improve success rates?",
        acceptedAnswer: {
          "@type": "Answer",
          text:
            "Multiple rounds let you challenge different inaccuracies, dispute with different parties, and respond to outcomes, increasing the chance that unverifiable items are removed or corrected.",
        },
      },
      {
        "@type": "Question",
        name: "What credit issues can we help address?",
        acceptedAnswer: {
          "@type": "Answer",
          text:
            "Common targets include inaccurate late payments, collections, charge-offs, incorrect balances/limits, duplicate accounts, and outdated or misreported account details.",
        },
      },
      {
        "@type": "Question",
        name: "Is Credit Clarity a substitute for legal advice?",
        acceptedAnswer: {
          "@type": "Answer",
          text:
            "No. We provide tools and educational guidance; for legal advice on your specific situation, consult a qualified attorney.",
        },
      },
      {
        "@type": "Question",
        name: "How do we analyze dispute letter effectiveness?",
        acceptedAnswer: {
          "@type": "Answer",
          text:
            "We track outcomes by item type, bureau, language patterns, and timing between rounds to continuously refine dispute strategies.",
        },
      },
      {
        "@type": "Question",
        name: "What makes AI-generated dispute letters more effective?",
        acceptedAnswer: {
          "@type": "Answer",
          text:
            "Letters can be personalized to the account and bureau, incorporate precise dispute reasons, and avoid repetitive boilerplate language that automated systems may deprioritize.",
        },
      },
      {
        "@type": "Question",
        name: "How does the process work from start to finish?",
        acceptedAnswer: {
          "@type": "Answer",
          text:
            "Upload reports, extract tradelines, generate a dispute strategy and letters per bureau, review for compliance, send disputes, then track responses and iterate with follow-up rounds.",
        },
      },
      {
        "@type": "Question",
        name: "What results can I expect from the dispute process?",
        acceptedAnswer: {
          "@type": "Answer",
          text:
            "Results vary. Many users see improvements over multiple rounds across several months depending on item type, accuracy of reporting, and creditor documentation.",
        },
      },
    ],
  };

  return (
    <>
      <Helmet>
        <title>FAQ - Credit Clarity | Credit Repair Questions Answered</title>
        <meta name="description" content="Find answers to common questions about credit repair, dispute letters, and how Credit Clarity's AI-powered platform helps improve your credit score." />
        <meta name="keywords" content="credit repair FAQ, credit dispute questions, credit score help, how does credit repair work" />
        <meta property="og:title" content="FAQ - Credit Clarity" />
        <meta property="og:description" content="Find answers to common questions about credit repair and how Credit Clarity helps improve your credit score." />
        <meta property="og:type" content="website" />
        <meta name="twitter:card" content="summary_large_image" />
        <meta name="twitter:title" content="FAQ - Credit Clarity" />
        <meta name="twitter:description" content="Find answers to common questions about credit repair and how Credit Clarity helps improve your credit score." />
        <link rel="canonical" href="https://creditclarity.ai/faq" />
        <script type="application/ld+json">{JSON.stringify(faqJsonLd)}</script>
      </Helmet>

      <div className="has-navbar">

        {/* Header */}
        <section className="relative overflow-hidden px-6 pt-24 pb-16 md:pt-32 md:pb-20">
          <div
            className="absolute inset-0 pointer-events-none"
            style={{
              background: 'radial-gradient(ellipse 80% 60% at 50% -10%, rgba(212,168,83,0.10) 0%, transparent 70%)',
            }}
          />
          <div className="relative max-w-3xl mx-auto text-center">
            <h1 className="text-5xl md:text-6xl font-extrabold mb-4" style={{ letterSpacing: '-0.03em' }}>
              <span className="text-gold-gradient">Frequently</span> Asked Questions
            </h1>
            <p className="text-muted-foreground text-lg">
              Understanding credit repair and our AI-powered dispute process
            </p>
          </div>
        </section>

        {/* Feature cards */}
        <section className="px-6 pb-16 max-w-5xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-16">
            {[
              {
                icon: FileText,
                title: 'Dispute Letters',
                desc: 'The legal foundation of credit repair through written disputes to bureaus and creditors.',
              },
              {
                icon: Brain,
                title: 'AI Analysis',
                desc: 'Our AI analyzes thousands of successful disputes to identify winning patterns.',
              },
              {
                icon: Rocket,
                title: 'Optimized Results',
                desc: 'Continuous improvement of dispute strategies based on real-world outcomes.',
              },
            ].map(({ icon: Icon, title, desc }) => (
              <div key={title} className="card-midnight rounded-xl p-8 text-center">
                <div className="p-3 rounded-full bg-[rgba(212,168,83,0.1)] w-14 h-14 flex items-center justify-center mx-auto mb-5">
                  <Icon className="h-6 w-6 text-[#D4A853]" />
                </div>
                <h3 className="text-lg font-semibold mb-2">{title}</h3>
                <p className="text-muted-foreground text-sm leading-relaxed">{desc}</p>
              </div>
            ))}
          </div>

          {/* Accordion */}
          <Accordion type="single" collapsible className="w-full space-y-3">
            {[
              {
                value: 'item-1',
                question: 'Why are dispute letters the foundation of credit repair?',
                answer: (
                  <div className="space-y-3 text-muted-foreground text-sm leading-relaxed">
                    <p>Dispute letters are the primary legal mechanism for challenging inaccurate information on your credit report. Under the Fair Credit Reporting Act (FCRA), you have the right to dispute any information you believe is inaccurate, untimely, misleading, incomplete, or unverifiable.</p>
                    <p>When you send a formal dispute letter, credit bureaus and creditors are legally required to investigate your claim within 30 days. If they cannot verify the information as accurate, they must remove it from your credit report.</p>
                    <p>This dispute process is a powerful legal right that puts the burden of proof on the credit bureaus and creditors, not on you.</p>
                  </div>
                ),
              },
              {
                value: 'item-2',
                question: 'How does sending multiple dispute letters improve success rates?',
                answer: (
                  <div className="space-y-3 text-muted-foreground text-sm leading-relaxed">
                    <p>Credit repair is often a process of persistence. Many consumers don't realize that sending a single dispute letter is rarely enough to resolve all credit issues.</p>
                    <p>When you send multiple strategically crafted dispute letters:</p>
                    <ul className="list-disc pl-5 space-y-1">
                      <li>You can address different aspects of the same negative item</li>
                      <li>You can dispute with multiple parties (bureaus, original creditors, collection agencies)</li>
                      <li>You create multiple opportunities for the item to be removed</li>
                      <li>You increase the chances that a creditor or bureau will miss the 30-day deadline</li>
                    </ul>
                    <p>Statistics show that consumers who send multiple rounds of disputes achieve significantly better results — improvement rates can increase by 30–40%.</p>
                  </div>
                ),
              },
              {
                value: 'item-3',
                question: 'What types of negative items can be disputed?',
                answer: (
                  <div className="space-y-3 text-muted-foreground text-sm leading-relaxed">
                    <p>Nearly any negative item can be disputed if it contains inaccuracies or cannot be properly verified. Common disputable items include:</p>
                    <ul className="list-disc pl-5 space-y-1">
                      <li><strong className="text-foreground">Late payments</strong> — dates, amounts, or account status may be incorrect</li>
                      <li><strong className="text-foreground">Collections</strong> — may lack proper documentation or violate verification requirements</li>
                      <li><strong className="text-foreground">Charge-offs</strong> — may contain inaccurate balance information or dates</li>
                      <li><strong className="text-foreground">Public records</strong> — bankruptcies, judgments, or liens that contain errors</li>
                      <li><strong className="text-foreground">Hard inquiries</strong> — unauthorized or duplicate inquiries</li>
                      <li><strong className="text-foreground">Account information</strong> — errors in credit limits, opening dates, or account status</li>
                    </ul>
                  </div>
                ),
              },
              {
                value: 'item-4',
                question: 'How does our AI enhance the dispute process?',
                answer: (
                  <div className="space-y-3 text-muted-foreground text-sm leading-relaxed">
                    <p><strong className="text-foreground">Advanced Pattern Recognition</strong> — Our AI analyzes thousands of successful dispute cases to identify which dispute reasons, letter formats, and language patterns lead to the highest success rates.</p>
                    <p><strong className="text-foreground">Bureau-Specific Optimization</strong> — The AI tailors dispute approaches based on which credit bureau you're dealing with, as each responds differently to various strategies.</p>
                    <p><strong className="text-foreground">Continuous Learning</strong> — Unlike traditional static methods, our AI continuously improves by learning from new successful disputes, adapting to changing bureau policies and legal precedents.</p>
                    <p><strong className="text-foreground">Personalized Strategy</strong> — Based on your specific credit situation, the AI recommends which items to dispute first and how to sequence multiple rounds for maximum impact.</p>
                  </div>
                ),
              },
              {
                value: 'item-5',
                question: 'How do we analyze dispute letter effectiveness?',
                answer: (
                  <div className="space-y-3 text-muted-foreground text-sm leading-relaxed">
                    <p>Our proprietary analysis system tracks success rates across multiple dimensions:</p>
                    <ul className="list-disc pl-5 space-y-1">
                      <li><strong className="text-foreground">Item-Specific Analysis</strong> — which dispute reasons work best for specific negative item types</li>
                      <li><strong className="text-foreground">Bureau-Specific Success Rates</strong> — what approaches work best with each credit bureau</li>
                      <li><strong className="text-foreground">Language Pattern Effectiveness</strong> — specific phrases and argument structures that drive higher success</li>
                      <li><strong className="text-foreground">Timing Optimization</strong> — how the timing between dispute letters affects outcomes</li>
                    </ul>
                  </div>
                ),
              },
              {
                value: 'item-6',
                question: 'What makes AI-generated dispute letters more effective?',
                answer: (
                  <div className="space-y-3 text-muted-foreground text-sm leading-relaxed">
                    <p>Traditional letters often fall into predictable patterns that bureaus process using automated systems. Our AI-generated letters offer:</p>
                    <ul className="list-disc pl-5 space-y-1">
                      <li><strong className="text-foreground">Strategic Personalization</strong> — uniquely crafted based on your specific situation</li>
                      <li><strong className="text-foreground">Legal Precision</strong> — incorporates FCRA provisions, CFPB guidance, and case law naturally</li>
                      <li><strong className="text-foreground">Evidence-Based Approach</strong> — specific arguments proven effective from our success data</li>
                      <li><strong className="text-foreground">Adaptive Language</strong> — adapts based on which bureau is being addressed and which round of disputes you're on</li>
                    </ul>
                  </div>
                ),
              },
              {
                value: 'item-7',
                question: 'How does the process work from start to finish?',
                answer: (
                  <ol className="list-decimal pl-5 space-y-2 text-muted-foreground text-sm leading-relaxed">
                    <li><strong className="text-foreground">Document Analysis</strong> — Upload your credit reports and our AI extracts all negative items, account information, and personal details.</li>
                    <li><strong className="text-foreground">Strategy Development</strong> — Our AI analyzes your credit situation and develops a personalized dispute strategy.</li>
                    <li><strong className="text-foreground">Letter Generation</strong> — Customized dispute letters are crafted for each bureau using high-success language patterns.</li>
                    <li><strong className="text-foreground">Quality Review</strong> — Each letter undergoes an AI-powered review for legal compliance and effectiveness.</li>
                    <li><strong className="text-foreground">Letter Sending</strong> — We provide the letters for you to send, or handle mailing through our secure system.</li>
                    <li><strong className="text-foreground">Response Tracking</strong> — Track bureau responses and investigation results through your dashboard.</li>
                    <li><strong className="text-foreground">Follow-up Strategy</strong> — Based on responses, our AI recommends follow-up dispute strategies.</li>
                  </ol>
                ),
              },
              {
                value: 'item-8',
                question: 'What results can I expect from the dispute process?',
                answer: (
                  <div className="space-y-3 text-muted-foreground text-sm leading-relaxed">
                    <p>While results vary, our data shows:</p>
                    <ul className="list-disc pl-5 space-y-1">
                      <li><strong className="text-foreground">First Round Success</strong> — approximately 20–30% of disputed items may be removed in round one</li>
                      <li><strong className="text-foreground">Cumulative Success</strong> — with 3–4 rounds, users have seen 50–70% of negative items removed or positively modified</li>
                      <li><strong className="text-foreground">Score Improvement</strong> — average credit score improvements of 40–100 points for users who complete the recommended process</li>
                    </ul>
                    <p>Key factors influencing success: age and type of negative items, quality of creditor documentation, persistence through multiple dispute rounds, and your credit activity during the dispute process.</p>
                  </div>
                ),
              },
            ].map(({ value, question, answer }) => (
              <AccordionItem
                key={value}
                value={value}
                className="card-midnight rounded-xl border-0 px-6"
              >
                <AccordionTrigger className="text-base font-semibold py-5 hover:text-[#D4A853] hover:no-underline transition-colors">
                  {question}
                </AccordionTrigger>
                <AccordionContent className="pb-5">
                  {answer}
                </AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
        </section>

      </div>
    </>
  );
}
