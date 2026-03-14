export default function TermsPage() {
  return (
    <div className="has-navbar">

      <div className="container max-w-3xl mx-auto py-16 px-4">
        <h1 className="text-3xl font-bold mb-2">
          Terms of <span className="text-gold-gradient">Service</span>
        </h1>
        <p className="text-sm text-muted-foreground mb-10">Last updated: March 8, 2026</p>

        <div className="prose prose-invert max-w-none space-y-8 text-sm leading-relaxed text-foreground/80">

          <section>
            <h2 className="text-lg font-semibold text-foreground mb-2">1. Acceptance of Terms</h2>
            <p>
              By accessing or using Credit Clarity, you agree to be bound by these Terms of Service.
              If you do not agree, do not use this service.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-foreground mb-2">2. Description of Service</h2>
            <p>
              Credit Clarity is a software tool that helps consumers generate FCRA-compliant dispute letters
              for their credit reports. We are not a law firm and do not provide legal advice. Dispute letters
              generated through our platform are templates; you are responsible for reviewing them before sending.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-foreground mb-2">3. Eligibility</h2>
            <p>
              You must be at least 18 years old and a resident of the United States to use this service.
              By creating an account, you represent that you meet these requirements.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-foreground mb-2">4. Account Responsibilities</h2>
            <p>
              You are responsible for maintaining the confidentiality of your account credentials.
              You agree to provide accurate information including your name, address, and SSN last 4 digits,
              and to update them if they change.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-foreground mb-2">5. No Guarantee of Results</h2>
            <p>
              We cannot guarantee that credit bureaus will remove disputed items from your credit report.
              Results depend on the validity of the dispute and the credit bureau's investigation. We offer
              a 30-day money-back guarantee if you are not satisfied with our service.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-foreground mb-2">6. Prohibited Use</h2>
            <p>You agree not to use Credit Clarity to:</p>
            <ul className="list-disc pl-5 space-y-1 mt-2">
              <li>Dispute accurate information on your credit report</li>
              <li>Submit disputes on behalf of another person without their consent</li>
              <li>Engage in identity theft or fraud</li>
              <li>Attempt to circumvent or reverse-engineer the platform</li>
            </ul>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-foreground mb-2">7. Subscription and Billing</h2>
            <p>
              Paid plans are billed monthly or annually as selected. You may cancel at any time from your
              account settings. Cancellations take effect at the end of the current billing period.
              No partial refunds are issued except under our 30-day guarantee.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-foreground mb-2">8. Limitation of Liability</h2>
            <p>
              To the maximum extent permitted by law, Credit Clarity shall not be liable for any indirect,
              incidental, or consequential damages arising from your use of the service. Our total liability
              shall not exceed the amount you paid in the 12 months preceding the claim.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-foreground mb-2">9. Changes to Terms</h2>
            <p>
              We may update these terms at any time. Continued use of the service after changes constitutes
              acceptance. We will notify you of material changes by email.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-foreground mb-2">10. Contact</h2>
            <p>
              Questions? Contact us at{" "}
              <a href="mailto:legal@creditclarity.ai" className="text-[#D4A853] hover:underline">
                legal@creditclarity.ai
              </a>.
            </p>
          </section>
        </div>
      </div>
    </div>
  );
}
