import { Helmet } from "react-helmet-async";

export default function PrivacyPage() {
  return (
    <div className="has-navbar">
      <Helmet>
        <title>Privacy Policy - Credit Clarity</title>
        <meta name="description" content="Credit Clarity privacy policy — how we collect, use, and protect your data." />
        <link rel="canonical" href="https://creditclarity.ai/privacy-policy" />
      </Helmet>

      <div className="container max-w-3xl mx-auto py-16 px-4">
        <h1 className="text-3xl font-bold mb-2">
          Privacy <span className="text-gold-gradient">Policy</span>
        </h1>
        <p className="text-sm text-muted-foreground mb-10">Last updated: March 8, 2026</p>

        <div className="prose prose-invert max-w-none space-y-8 text-sm leading-relaxed text-foreground/80">

          <section>
            <h2 className="text-lg font-semibold text-foreground mb-2">1. Information We Collect</h2>
            <p>
              When you use Credit Clarity, we collect information you provide directly — including your name,
              mailing address, last four digits of your Social Security Number, and uploaded credit report documents.
              We never collect or store your full Social Security Number.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-foreground mb-2">2. How We Use Your Information</h2>
            <p>We use your information solely to:</p>
            <ul className="list-disc pl-5 space-y-1 mt-2">
              <li>Generate personalized FCRA-compliant dispute letters on your behalf</li>
              <li>Store and display your dispute history within your account</li>
              <li>Communicate with you about the status of your account</li>
              <li>Improve our AI models in an anonymized, aggregated manner</li>
            </ul>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-foreground mb-2">3. Data Storage and Security</h2>
            <p>
              Your data is stored securely using Supabase, which employs AES-256 encryption at rest and
              TLS in transit. Profile data and dispute letters are accessible only to your authenticated
              account. We apply row-level security policies to enforce this at the database layer.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-foreground mb-2">4. AI Processing</h2>
            <p>
              Dispute letter content may be sent to OpenAI's API for generation. We do not share personally
              identifiable information with OpenAI beyond what is necessary to generate the letter (name,
              masked SSN, address, and disputed account details). OpenAI's data handling policies apply to
              this processing.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-foreground mb-2">5. Data Retention</h2>
            <p>
              We retain your data for as long as your account is active or as needed to provide our service.
              You may request deletion of your account and all associated data by contacting us at
              privacy@creditclarity.ai.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-foreground mb-2">6. Your Rights</h2>
            <p>
              Depending on your jurisdiction, you may have rights to access, correct, or delete your personal
              data. To exercise these rights, contact us at privacy@creditclarity.ai.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-foreground mb-2">7. Contact</h2>
            <p>
              Questions about this policy? Email us at{" "}
              <a href="mailto:privacy@creditclarity.ai" className="text-[#D4A853] hover:underline">
                privacy@creditclarity.ai
              </a>.
            </p>
          </section>
        </div>
      </div>
    </div>
  );
}
