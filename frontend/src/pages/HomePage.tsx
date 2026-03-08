import React from 'react';
import { Link } from 'react-router-dom';
import { Helmet } from "react-helmet-async";
import { Button } from "@/components/ui/button";
import { Shield, TrendingUp, FileText, Star, ArrowRight, CheckCircle } from "lucide-react";

const HomePage = React.memo(function HomePage() {
  return (
    <>
      <Helmet>
        <title>Credit Clarity AI Assist - Improve Your Credit Score</title>
        <meta name="description" content="AI-powered platform to analyze, dispute, and improve your credit score with Credit Clarity." />
        <meta name="keywords" content="credit repair, credit score, dispute, credit clarity, AI credit assistant" />
        <meta name="robots" content="index, follow" />
        <link rel="canonical" href="https://creditclarity.com/" />
        <meta property="og:title" content="Credit Clarity AI Assist - Improve Your Credit Score" />
        <meta property="og:description" content="AI-powered platform to analyze, dispute, and improve your credit score." />
        <meta property="og:type" content="website" />
        <meta property="og:url" content="https://creditclarity.com/" />
      </Helmet>

      <div className="has-navbar">

        {/* Hero Section */}
        <section className="relative overflow-hidden px-6 pt-24 pb-20 md:pt-32 md:pb-28">
          {/* Background glow */}
          <div
            className="absolute inset-0 pointer-events-none"
            style={{
              background: 'radial-gradient(ellipse 80% 60% at 50% -10%, rgba(212,168,83,0.12) 0%, transparent 70%)',
            }}
          />

          <div className="relative max-w-4xl mx-auto text-center">
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-[rgba(212,168,83,0.3)] bg-[rgba(212,168,83,0.06)] text-sm text-[#D4A853] font-medium mb-8">
              <Star className="h-3.5 w-3.5 fill-current" />
              AI-Powered Credit Repair Platform
            </div>

            <h1
              className="text-5xl md:text-6xl lg:text-7xl font-extrabold mb-6 leading-tight"
              style={{ letterSpacing: '-0.03em' }}
            >
              Take Control of{' '}
              <span className="text-gold-gradient">Your Credit</span>
            </h1>

            <p className="text-xl text-muted-foreground max-w-2xl mx-auto mb-10 leading-relaxed">
              Analyze your credit reports, generate professional dispute letters,
              and track improvements — all powered by AI.
            </p>

            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link to="/signup">
                <Button size="lg" className="btn-gold rounded-md px-8 text-base h-12">
                  Get Started Free
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              </Link>
              <Link to="/pricing">
                <Button
                  size="lg"
                  variant="ghost"
                  className="rounded-md px-8 text-base h-12 text-muted-foreground hover:text-foreground hover:bg-white/5"
                >
                  View Pricing
                </Button>
              </Link>
            </div>

            {/* Social proof strip */}
            <div className="mt-12 flex flex-wrap items-center justify-center gap-6 text-sm text-muted-foreground">
              {['No credit card required', 'Cancel anytime', '30-day money-back guarantee'].map((item) => (
                <span key={item} className="flex items-center gap-1.5">
                  <CheckCircle className="h-4 w-4 text-[#22C55E]" />
                  {item}
                </span>
              ))}
            </div>
          </div>
        </section>

        {/* Stats bar */}
        <section className="border-y border-[#1E2D47] bg-[rgba(26,35,64,0.4)]">
          <div className="max-w-5xl mx-auto px-6 py-8 grid grid-cols-1 sm:grid-cols-3 gap-8 text-center">
            {[
              { value: '10,000+', label: 'Disputes Filed' },
              { value: '94%', label: 'Success Rate' },
              { value: '45 Days', label: 'Avg. Resolution' },
            ].map(({ value, label }) => (
              <div key={label}>
                <p className="text-3xl font-bold text-gold-gradient mb-1">{value}</p>
                <p className="text-sm text-muted-foreground">{label}</p>
              </div>
            ))}
          </div>
        </section>

        {/* How It Works */}
        <section className="px-6 py-20 max-w-6xl mx-auto">
          <div className="text-center mb-14">
            <h2 className="text-3xl md:text-4xl font-bold mb-4" style={{ letterSpacing: '-0.02em' }}>
              How It Works
            </h2>
            <p className="text-muted-foreground max-w-xl mx-auto">
              Three simple steps to start improving your credit score today.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[
              {
                step: '01',
                icon: FileText,
                title: 'Upload Your Report',
                desc: 'Upload your credit reports from Equifax, Experian, or TransUnion. Our AI analyzes every tradeline.',
              },
              {
                step: '02',
                icon: Shield,
                title: 'AI Finds Errors',
                desc: 'We identify inaccuracies, outdated items, and disputable entries that may be hurting your score.',
              },
              {
                step: '03',
                icon: TrendingUp,
                title: 'Dispute & Improve',
                desc: 'Generate professional dispute letters and track your credit score improvements over time.',
              },
            ].map(({ step, icon: Icon, title, desc }) => (
              <div key={step} className="card-midnight p-8 rounded-xl group">
                <div className="flex items-start gap-4 mb-5">
                  <span
                    className="text-xs font-bold tracking-widest text-[#D4A853] opacity-60 mt-1"
                    style={{ fontVariantNumeric: 'tabular-nums' }}
                  >
                    {step}
                  </span>
                  <div className="p-2 rounded-lg bg-[rgba(212,168,83,0.1)]">
                    <Icon className="h-5 w-5 text-[#D4A853]" />
                  </div>
                </div>
                <h3 className="text-lg font-semibold mb-2">{title}</h3>
                <p className="text-muted-foreground text-sm leading-relaxed">{desc}</p>
              </div>
            ))}
          </div>
        </section>

        {/* CTA Banner */}
        <section className="px-6 pb-24">
          <div
            className="max-w-4xl mx-auto rounded-2xl p-12 text-center"
            style={{
              background: 'linear-gradient(135deg, rgba(212,168,83,0.12) 0%, rgba(59,127,212,0.08) 100%)',
              border: '1px solid rgba(212,168,83,0.2)',
            }}
          >
            <h2 className="text-3xl md:text-4xl font-bold mb-4" style={{ letterSpacing: '-0.02em' }}>
              Ready to Fix Your Credit?
            </h2>
            <p className="text-muted-foreground mb-8 max-w-xl mx-auto">
              Join thousands of users who have already improved their credit scores with CreditClarity.
            </p>
            <Link to="/signup">
              <Button size="lg" className="btn-gold rounded-md px-10 text-base h-12">
                Start For Free
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </Link>
          </div>
        </section>

      </div>
    </>
  );
});

export default HomePage;
