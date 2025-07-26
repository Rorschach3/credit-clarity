
import React from "react";
import MainLayout from "@/components/layout/MainLayout";
import { Accordion, AccordionItem, AccordionTrigger, AccordionContent } from "@/components/ui/accordion";
import { FileText, Brain, Rocket } from "lucide-react";

export default function FaqPage() {
  return (
    <MainLayout>
      <div className="container py-12 max-w-4xl mx-auto">
        <h1 className="text-4xl font-bold text-center mb-2">Frequently Asked Questions</h1>
        <p className="text-center text-gray-600 mb-12">Understanding Credit Repair and Our AI-Powered Dispute Process</p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-12">
          <div className="flex flex-col items-center text-center p-6 bg-white rounded-lg shadow-sm border border-gray-100">
            <div className="bg-blue-100 p-3 rounded-full mb-4">
              <FileText className="h-6 w-6 text-blue-600" />
            </div>
            <h3 className="text-xl font-semibold mb-2">Dispute Letters</h3>
            <p className="text-gray-600">The legal foundation of credit repair through written disputes to bureaus and creditors.</p>
          </div>
          
          <div className="flex flex-col items-center text-center p-6 bg-white rounded-lg shadow-sm border border-gray-100">
            <div className="bg-purple-100 p-3 rounded-full mb-4">
              <Brain className="h-6 w-6 text-purple-600" />
            </div>
            <h3 className="text-xl font-semibold mb-2">AI Analysis</h3>
            <p className="text-gray-600">Our AI analyzes thousands of successful disputes to identify winning patterns.</p>
          </div>
          
          <div className="flex flex-col items-center text-center p-6 bg-white rounded-lg shadow-sm border border-gray-100">
            <div className="bg-green-100 p-3 rounded-full mb-4">
              <Rocket className="h-6 w-6 text-green-600" />
            </div>
            <h3 className="text-xl font-semibold mb-2">Optimized Results</h3>
            <p className="text-gray-600">Continuous improvement of dispute strategies based on real-world outcomes.</p>
          </div>
        </div>

        <Accordion type="single" collapsible className="w-full">
          <AccordionItem value="item-1">
            <AccordionTrigger className="text-xl font-semibold">
              Why are dispute letters the foundation of credit repair?
            </AccordionTrigger>
            <AccordionContent className="text-gray-700 space-y-4">
              <p>
                Dispute letters are the primary legal mechanism for challenging inaccurate information on your credit report. Under the Fair Credit Reporting Act (FCRA), you have the right to dispute any information you believe is inaccurate, untimely, misleading, incomplete, or unverifiable.
              </p>
              <p>
                When you send a formal dispute letter, credit bureaus and creditors are legally required to investigate your claim within 30 days (in most cases). If they cannot verify the information as accurate, they must remove it from your credit report.
              </p>
              <p>
                This dispute process is not just a formality—it's a powerful legal right that puts the burden of proof on the credit bureaus and creditors, not on you.
              </p>
            </AccordionContent>
          </AccordionItem>

          <AccordionItem value="item-2">
            <AccordionTrigger className="text-xl font-semibold">
              How does sending multiple dispute letters improve success rates?
            </AccordionTrigger>
            <AccordionContent className="text-gray-700 space-y-4">
              <p>
                Credit repair is often a process of persistence. Many consumers don't realize that sending a single dispute letter is rarely enough to resolve all credit issues.
              </p>
              <p>
                When you send multiple strategically crafted dispute letters:
              </p>
              <ul className="list-disc pl-5 space-y-2">
                <li>You can address different aspects of the same negative item</li>
                <li>You can dispute with multiple parties (bureaus, original creditors, collection agencies)</li>
                <li>You create multiple opportunities for the item to be removed during verification attempts</li>
                <li>You increase the chances that a creditor or bureau will miss the 30-day investigation deadline</li>
              </ul>
              <p>
                Statistics show that consumers who send multiple rounds of disputes achieve significantly better results than those who send just one letter. The improvement rate can increase by as much as 30-40% with persistent, strategic disputing.
              </p>
            </AccordionContent>
          </AccordionItem>

          <AccordionItem value="item-3">
            <AccordionTrigger className="text-xl font-semibold">
              What types of negative items can be disputed?
            </AccordionTrigger>
            <AccordionContent className="text-gray-700 space-y-4">
              <p>
                Nearly any negative item on your credit report can be disputed if you believe it contains inaccuracies or cannot be properly verified. Common disputable items include:
              </p>
              <ul className="list-disc pl-5 space-y-2">
                <li><strong>Late payments:</strong> Dates, amounts, or account status may be reported incorrectly</li>
                <li><strong>Collections:</strong> May lack proper documentation or violate verification requirements</li>
                <li><strong>Charge-offs:</strong> May contain inaccurate balance information or dates</li>
                <li><strong>Public records:</strong> Including bankruptcies, judgments, or liens that contain errors</li>
                <li><strong>Hard inquiries:</strong> That you did not authorize or are duplicative</li>
                <li><strong>Account information:</strong> Including errors in credit limits, account opening dates, or account status</li>
              </ul>
              <p>
                Even accounts that are legitimately yours may contain disputable errors in how they're being reported—the date, amount, status, or other details may be incorrect.
              </p>
            </AccordionContent>
          </AccordionItem>

          <AccordionItem value="item-4">
            <AccordionTrigger className="text-xl font-semibold">
              How does our AI enhance the dispute process?
            </AccordionTrigger>
            <AccordionContent className="text-gray-700 space-y-4">
              <p>
                Our AI-powered system represents a revolutionary advancement in credit repair technology:
              </p>
              <p>
                <strong>Advanced Pattern Recognition:</strong> Our AI analyzes thousands of successful dispute cases to identify which dispute reasons, letter formats, and specific language patterns lead to the highest success rates for particular types of negative items.
              </p>
              <p>
                <strong>Bureau-Specific Optimization:</strong> The AI tailors dispute approaches based on which credit bureau you're dealing with, as each has different internal processes and responds differently to various dispute strategies.
              </p>
              <p>
                <strong>Continuous Learning:</strong> Unlike traditional dispute methods that remain static, our AI continuously improves by learning from new successful disputes, adapting to changing bureau policies and legal precedents.
              </p>
              <p>
                <strong>Personalized Dispute Strategy:</strong> Based on your specific credit situation, the AI recommends which items to dispute first, which dispute reasons to use, and how to sequence multiple rounds of disputes for maximum impact.
              </p>
            </AccordionContent>
          </AccordionItem>

          <AccordionItem value="item-5">
            <AccordionTrigger className="text-xl font-semibold">
              How do we analyze dispute letter effectiveness?
            </AccordionTrigger>
            <AccordionContent className="text-gray-700 space-y-4">
              <p>
                Our proprietary dispute letter analysis system tracks success rates across multiple dimensions:
              </p>
              <ul className="list-disc pl-5 space-y-2">
                <li><strong>Item-Specific Analysis:</strong> We track which dispute reasons and letter formats work best for specific types of negative items (e.g., medical collections vs. credit card charge-offs)</li>
                <li><strong>Bureau-Specific Success Rates:</strong> We analyze which approaches work best with each specific credit bureau</li>
                <li><strong>Language Pattern Effectiveness:</strong> Our AI identifies specific phrases, citation styles, and argument structures that lead to higher success rates</li>
                <li><strong>Timing Optimization:</strong> We analyze how the timing between dispute letters affects success rates</li>
              </ul>
              <p>
                This multi-faceted analysis allows us to continuously refine our dispute letter templates, creating a constantly evolving and improving system that stays ahead of credit bureau verification processes.
              </p>
            </AccordionContent>
          </AccordionItem>

          <AccordionItem value="item-6">
            <AccordionTrigger className="text-xl font-semibold">
              What makes AI-generated dispute letters more effective?
            </AccordionTrigger>
            <AccordionContent className="text-gray-700 space-y-4">
              <p>
                Traditional dispute letters often fall into predictable patterns that credit bureaus can easily identify and process using automated systems. Our AI-generated letters offer several advantages:
              </p>
              <ul className="list-disc pl-5 space-y-2">
                <li><strong>Strategic Personalization:</strong> Each letter is uniquely crafted based on your specific credit situation, avoiding template recognition</li>
                <li><strong>Legal Precision:</strong> Our AI incorporates relevant FCRA provisions, CFPB guidance, and case law citations in a natural, non-formulaic way</li>
                <li><strong>Evidence-Based Approach:</strong> Letters include specific details and arguments that have proven effective based on our success data</li>
                <li><strong>Adaptive Language:</strong> The AI adapts its language and approach based on which bureau is being addressed and which round of disputes you're on</li>
              </ul>
              <p>
                By avoiding common template language and incorporating sophisticated legal arguments in a natural way, our letters are more likely to trigger manual review rather than automated rejection.
              </p>
            </AccordionContent>
          </AccordionItem>

          <AccordionItem value="item-7">
            <AccordionTrigger className="text-xl font-semibold">
              How does the process work from start to finish?
            </AccordionTrigger>
            <AccordionContent className="text-gray-700 space-y-4">
              <p>
                Our AI-powered dispute process follows these steps:
              </p>
              <ol className="list-decimal pl-5 space-y-3">
                <li>
                  <strong>Document Analysis:</strong> Upload your credit reports and our AI extracts all negative items, account information, and personal details.
                </li>
                <li>
                  <strong>Strategy Development:</strong> Our AI analyzes your specific credit situation and develops a personalized dispute strategy, identifying which items to dispute first and which approaches to use.
                </li>
                <li>
                  <strong>Letter Generation:</strong> The AI crafts customized dispute letters for each bureau, incorporating language patterns and dispute reasons with proven success rates.
                </li>
                <li>
                  <strong>Quality Review:</strong> Each letter undergoes an AI-powered review to ensure legal compliance, effectiveness, and quality.
                </li>
                <li>
                  <strong>Letter Sending:</strong> We can either provide the letters for you to send, or handle the mailing process for you through our secure mailing system.
                </li>
                <li>
                  <strong>Response Tracking:</strong> Track bureau responses and investigation results through your dashboard.
                </li>
                <li>
                  <strong>Follow-up Strategy:</strong> Based on responses received, our AI recommends follow-up dispute strategies, adapting the approach based on each bureau's specific response.
                </li>
              </ol>
              <p>
                Throughout this process, our system is learning from results and continually refining its approach, ensuring that your dispute strategy becomes more effective over time.
              </p>
            </AccordionContent>
          </AccordionItem>

          <AccordionItem value="item-8">
            <AccordionTrigger className="text-xl font-semibold">
              What results can I expect from the dispute process?
            </AccordionTrigger>
            <AccordionContent className="text-gray-700 space-y-4">
              <p>
                While results vary based on individual credit situations, our data shows:
              </p>
              <ul className="list-disc pl-5 space-y-2">
                <li><strong>First Round Success:</strong> Approximately 20-30% of disputed items may be removed in the first round of disputes</li>
                <li><strong>Cumulative Success:</strong> With 3-4 rounds of strategic disputes, our users have seen 50-70% of negative items removed or positively modified</li>
                <li><strong>Score Improvement:</strong> Average credit score improvements of 40-100 points for users who complete the recommended dispute process</li>
              </ul>
              <p>
                Important factors that influence success rates include:
              </p>
              <ul className="list-disc pl-5 space-y-2">
                <li>The age and type of negative items</li>
                <li>The quality of documentation maintained by creditors</li>
                <li>Your persistence in following through with multiple rounds of disputes</li>
                <li>Your credit activity during the dispute process</li>
              </ul>
              <p>
                Our system provides realistic expectations based on your specific credit profile and continuously adapts its strategy based on interim results.
              </p>
            </AccordionContent>
          </AccordionItem>
        </Accordion>
      </div>
    </MainLayout>
  );
}
