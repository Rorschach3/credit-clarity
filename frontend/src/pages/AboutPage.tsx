import { Button } from "@/components/ui/button";
import { Link } from "react-router-dom";
import { Shield, UserCheck, BookOpen, ArrowRight } from "lucide-react";
import { Helmet } from "react-helmet-async";

export default function AboutPage() {
  const teamMembers = [
    {
      name: "Jane Cooper",
      title: "CEO & Founder",
      image: "https://images.unsplash.com/photo-1494790108377-be9c29b29330?ixlib=rb-1.2.1&auto=format&fit=facearea&facepad=2&w=256&h=256&q=80"
    },
    {
      name: "Robert Fox",
      title: "Chief Technology Officer",
      image: "https://images.unsplash.com/photo-1570295999919-56ceb5ecca61?ixlib=rb-1.2.1&auto=format&fit=facearea&facepad=2&w=256&h=256&q=80"
    },
    {
      name: "Leslie Alexander",
      title: "Head of AI Development",
      image: "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?ixlib=rb-1.2.1&auto=format&fit=facearea&facepad=2&w=256&h=256&q=80"
    },
    {
      name: "Michael Johnson",
      title: "Credit Expert",
      image: "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?ixlib=rb-1.2.1&auto=format&fit=facearea&facepad=2&w=256&h=256&q=80"
    }
  ];

  return (
    <>
      <Helmet>
        <title>About Us - Credit Clarity | AI-Powered Credit Repair</title>
        <meta name="description" content="Learn about Credit Clarity's mission to help Americans improve their credit scores through AI-powered credit report analysis and dispute letter generation." />
        <meta name="keywords" content="credit repair, about credit clarity, AI credit repair, credit score improvement, credit report analysis" />
        <meta property="og:title" content="About Us - Credit Clarity" />
        <meta property="og:description" content="Learn about Credit Clarity's mission to help Americans improve their credit scores through AI-powered credit report analysis." />
        <meta property="og:type" content="website" />
        <meta name="twitter:card" content="summary_large_image" />
        <meta name="twitter:title" content="About Us - Credit Clarity" />
        <meta name="twitter:description" content="Learn about Credit Clarity's mission to help Americans improve their credit scores through AI-powered credit report analysis." />
        <link rel="canonical" href="https://creditclarity.ai/about" />
      </Helmet>

      <div className="has-navbar">

        {/* Hero Section */}
        <section className="relative overflow-hidden px-6 pt-24 pb-20 md:pt-32 md:pb-28">
          <div
            className="absolute inset-0 pointer-events-none"
            style={{
              background: 'radial-gradient(ellipse 80% 60% at 50% -10%, rgba(212,168,83,0.12) 0%, transparent 70%)',
            }}
          />
          <div className="relative max-w-3xl mx-auto text-center">
            <h1 className="text-5xl md:text-6xl font-extrabold mb-6 leading-tight" style={{ letterSpacing: '-0.03em' }}>
              About <span className="text-gold-gradient">Credit Clarity</span>
            </h1>
            <p className="text-xl text-muted-foreground mb-10 leading-relaxed">
              We're on a mission to help millions of Americans improve their credit scores through the power of artificial intelligence.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link to="/signup">
                <Button size="lg" className="btn-gold rounded-md px-8 text-base h-12">
                  Get Started
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              </Link>
              <Link to="/contact">
                <Button size="lg" variant="ghost" className="rounded-md px-8 text-base h-12 text-muted-foreground hover:text-foreground hover:bg-white/5">
                  Contact Us
                </Button>
              </Link>
            </div>
          </div>
        </section>

        {/* Our Story */}
        <section className="px-6 py-20 max-w-3xl mx-auto">
          <h2 className="text-3xl md:text-4xl font-bold mb-8 text-center" style={{ letterSpacing: '-0.02em' }}>
            Our Story
          </h2>
          <div className="card-midnight rounded-xl p-8 space-y-4 text-muted-foreground leading-relaxed">
            <p>
              CreditClarityAI was founded in 2024 with a simple idea: what if we could use artificial intelligence to make credit repair more accessible, affordable, and effective for everyday Americans?
            </p>
            <p>
              Our founder, a former credit analyst, saw firsthand how errors on credit reports were causing major financial hardships for consumers. At the same time, traditional credit repair companies were charging high fees with questionable results.
            </p>
            <p>
              By combining cutting-edge OCR technology with advanced AI models trained on thousands of successful dispute letters, we've created a platform that can identify errors on credit reports with incredible accuracy and generate customized dispute letters that get results.
            </p>
            <p>
              Today, CreditClarityAI has helped thousands of customers improve their credit scores, saving them money on mortgages, auto loans, and credit cards while opening doors to better financial opportunities.
            </p>
          </div>
        </section>

        {/* Core Values */}
        <section className="px-6 py-20 border-y border-[#1E2D47] bg-[rgba(26,35,64,0.3)]">
          <div className="max-w-5xl mx-auto">
            <div className="text-center mb-14">
              <h2 className="text-3xl md:text-4xl font-bold mb-4" style={{ letterSpacing: '-0.02em' }}>
                Our Core Values
              </h2>
              <p className="text-muted-foreground">The principles that guide everything we do</p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {[
                {
                  icon: Shield,
                  title: 'Transparency',
                  desc: "We're honest and upfront about what our service can and cannot do, with fair pricing and no hidden fees.",
                },
                {
                  icon: BookOpen,
                  title: 'Education',
                  desc: 'We believe in empowering our customers with knowledge about credit repair, scoring, and financial literacy.',
                },
                {
                  icon: UserCheck,
                  title: 'Customer Success',
                  desc: "We measure our success by the improvements in our customers' credit scores and financial opportunities.",
                },
              ].map(({ icon: Icon, title, desc }) => (
                <div key={title} className="card-midnight p-8 rounded-xl text-center">
                  <div className="p-3 rounded-full bg-[rgba(212,168,83,0.1)] w-14 h-14 flex items-center justify-center mx-auto mb-5">
                    <Icon className="h-6 w-6 text-[#D4A853]" />
                  </div>
                  <h3 className="text-xl font-semibold mb-3">{title}</h3>
                  <p className="text-muted-foreground text-sm leading-relaxed">{desc}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Stats */}
        <section className="border-b border-[#1E2D47] bg-[rgba(26,35,64,0.4)]">
          <div className="max-w-5xl mx-auto px-6 py-16 grid grid-cols-1 sm:grid-cols-3 gap-8 text-center">
            {[
              { value: '15,000+', label: 'Customers Served' },
              { value: '85%', label: 'Success Rate' },
              { value: '+68 pts', label: 'Avg. Score Increase' },
            ].map(({ value, label }) => (
              <div key={label}>
                <p className="text-4xl font-bold text-gold-gradient mb-2">{value}</p>
                <p className="text-sm text-muted-foreground">{label}</p>
              </div>
            ))}
          </div>
        </section>

        {/* Team */}
        <section className="px-6 py-20 max-w-5xl mx-auto">
          <div className="text-center mb-14">
            <h2 className="text-3xl md:text-4xl font-bold mb-4" style={{ letterSpacing: '-0.02em' }}>
              Our Team
            </h2>
            <p className="text-muted-foreground">Meet the experts behind CreditClarityAI</p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
            {teamMembers.map((member) => (
              <div key={member.name} className="card-midnight rounded-xl p-6 text-center">
                <img
                  src={member.image}
                  alt={member.name}
                  className="w-20 h-20 rounded-full mx-auto mb-4 object-cover ring-2 ring-[rgba(212,168,83,0.2)]"
                />
                <h3 className="font-semibold mb-1">{member.name}</h3>
                <p className="text-sm text-muted-foreground">{member.title}</p>
              </div>
            ))}
          </div>
        </section>

        {/* CTA */}
        <section className="px-6 pb-24">
          <div
            className="max-w-4xl mx-auto rounded-2xl p-12 text-center"
            style={{
              background: 'linear-gradient(135deg, rgba(212,168,83,0.12) 0%, rgba(59,127,212,0.08) 100%)',
              border: '1px solid rgba(212,168,83,0.2)',
            }}
          >
            <h2 className="text-3xl md:text-4xl font-bold mb-4" style={{ letterSpacing: '-0.02em' }}>
              Ready to Improve Your Credit?
            </h2>
            <p className="text-muted-foreground mb-8 max-w-xl mx-auto">
              Join thousands of customers who have successfully improved their credit scores with CreditClarityAI.
            </p>
            <Link to="/signup">
              <Button size="lg" className="btn-gold rounded-md px-10 text-base h-12">
                Get Started Today
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </Link>
          </div>
        </section>

      </div>
    </>
  );
}
