import { useState } from "react";

import { Button } from "@/components/ui/button";
import {Card, CardContent, CardFooter, CardHeader, CardTitle} from "@/components/ui/card";
import { CheckCircle2 } from "lucide-react";
import { toast } from "sonner";
import { supabase } from "@/integrations/supabase/client";
import { useAuth } from "@/hooks/use-auth";
import { useNavigate } from "react-router-dom";
import { Helmet } from "react-helmet-async";

export default function PricingPage() {
  const [billingCycle, setBillingCycle] = useState<"monthly" | "yearly">("monthly");
  const [isLoading, setIsLoading] = useState<string | null>(null);
  const { user } = useAuth();
  const navigate = useNavigate();

  const plans = [
    {
      id: "free",
      name: "Free",
      description: "Get started for free",
      price: 0,
      features: [
        "Basic credit report analysis",
        "1 dispute letter to one bureau",
        "Email support"
      ],
      recommended: false,
      priceId: "free" // No price ID needed for free tier
    },
    {
      id: "plus",
      name: "Plus",
      description: "Our most popular credit repair plan",
      price: billingCycle === "monthly" ? 25 : 250,
      features: [
        "Dispute letters for all negative items (up to 8)",
        "Advanced AI credit report analysis",
        "Priority mail delivery with tracking",
        "Response validation assistance",
        "Priority email & chat support"
      ],
      recommended: true,
      priceId: billingCycle === "monthly" ? "price_plus_monthly" : "price_plus_yearly"
    },
    {
      id: "pro",
      name: "Pro",
      description: "Maximum credit repair coverage",
      price: billingCycle === "monthly" ? 50 : 500,
      features: [
        "Everything in Plus",
        "Dispute letters sent to credit bureaus AND creditors",
        "Advanced credit score tracking",
        "Certified mail delivery",
        "Dedicated account manager",
        "Phone support"
      ],
      recommended: false,
      priceId: billingCycle === "monthly" ? "price_pro_monthly" : "price_pro_yearly"
    }
  ];

  const handleSubscribe = async (plan: typeof plans[0]) => {
    if (plan.id === "free") {
      toast.info("Free plan doesn't require subscription");
      navigate("/dispute-generator");
      return;
    }
    
    if (!user) {
      toast.info("Please log in to subscribe");
      navigate("/login", { state: { returnTo: "/pricing" } });
      return;
    }

    try {
      setIsLoading(plan.id);
      
      const { data, error } = await supabase.functions.invoke('create-checkout', {
        body: { priceId: plan.priceId },
      });
      
      if (error) throw new Error(error.message);
      if (!data?.url) throw new Error("No checkout URL returned");
      
      // Redirect to Stripe Checkout
      window.location.href = data.url;
    } catch (error) {
      console.error('Error creating checkout session:', error);
      toast.error("Could not initiate subscription process. Please try again.");
    } finally {
      setIsLoading(null);
    }
  };

  return (
   <div className="has-navbar">
    <Helmet>
      <title>Pricing Plans - Credit Clarity | Affordable Credit Repair</title>
      <meta name="description" content="Choose from flexible pricing plans for AI-powered credit repair. From free basic analysis to unlimited dispute letters with expert support." />
      <meta name="keywords" content="credit repair pricing, affordable credit repair, credit repair plans, credit score improvement cost" />
      <meta property="og:title" content="Pricing Plans - Credit Clarity" />
      <meta property="og:description" content="Choose from flexible pricing plans for AI-powered credit repair. From free basic analysis to unlimited dispute letters." />
      <meta property="og:type" content="website" />
      <meta name="twitter:card" content="summary_large_image" />
      <meta name="twitter:title" content="Pricing Plans - Credit Clarity" />
      <meta name="twitter:description" content="Choose from flexible pricing plans for AI-powered credit repair." />
      <link rel="canonical" href="https://creditclarity.ai/pricing" />
    </Helmet>

    <div className="py-16 px-4 container">
     <div className="max-w-3xl mx-auto text-center mb-12">
      <h1 className="text-4xl font-bold mb-4">Simple, Transparent Pricing</h1>
      <p className="text-xl text-muted-foreground mb-8">
       Choose the plan that fits your credit repair needs
      </p>

      <div className="inline-flex items-center p-1 bg-[#1A2340] rounded-lg mb-8 border border-[#1E2D47]">
       <button
        onClick={() => setBillingCycle("monthly")}
        className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
         billingCycle === "monthly"
          ? "bg-[#D4A853] text-[#0F1629] shadow-sm"
          : "text-muted-foreground hover:text-foreground"
        }`}
       >
        Monthly
       </button>
       <button
        onClick={() => setBillingCycle("yearly")}
        className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
         billingCycle === "yearly"
          ? "bg-[#D4A853] text-[#0F1629] shadow-sm"
          : "text-muted-foreground hover:text-foreground"
        }`}
       >
        Yearly <span className="text-xs text-[#22C55E] font-medium ml-1">Save 17%</span>
       </button>
      </div>
     </div>

     <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-6xl mx-auto">
      {plans.map((plan) => (
       <Card
        key={plan.id}
        className={`relative card-midnight ${
         plan.recommended ? "border-[rgba(212,168,83,0.4)] shadow-gold" : ""
        }`}
       >
        {plan.recommended && (
         <div className="absolute -top-4 left-0 right-0 mx-auto w-max bg-[#D4A853] text-[#0F1629] px-4 py-1 rounded-full text-sm font-bold">
          Most Popular
         </div>
        )}
        <CardHeader>
         <CardTitle className="text-2xl">{plan.name}</CardTitle>
         <p className="text-muted-foreground mt-2">{plan.description}</p>
        </CardHeader>
        <CardContent>
         <div className="mb-6">
          <p className="text-4xl font-bold">${plan.price}</p>
          <p className="text-muted-foreground text-sm">per {billingCycle === "monthly" ? "month" : "year"}</p>
         </div>
         <ul className="space-y-3">
          {plan.features.map((feature, i) => (
           <li key={i} className="flex items-start">
            <CheckCircle2 className="h-5 w-5 text-green-500 mr-2 shrink-0 mt-0.5" />
            <span>{feature}</span>
           </li>
          ))}
         </ul>
        </CardContent>
        <CardFooter>
         <Button
          className={`w-full ${plan.recommended ? "btn-gold" : "btn-gold-outline"}`}
          onClick={() => handleSubscribe(plan)}
          disabled={isLoading === plan.id}
         >
          {plan.id === "free" ? "Get Started" : isLoading === plan.id ? "Loading..." : "Subscribe"}
         </Button>
        </CardFooter>
       </Card>
      ))}
     </div>

     <div className="max-w-3xl mx-auto mt-16 text-center">
      <h2 className="text-2xl font-bold mb-4">Frequently Asked Questions</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-left mt-8">
       <div>
        <h3 className="font-semibold text-lg mb-2">How does the service work?</h3>
        <p className="text-muted-foreground">
         Upload your credit reports, and our AI will analyze them to identify errors. We then generate and mail professionally formatted dispute letters to credit bureaus on your behalf.
        </p>
       </div>
       <div>
        <h3 className="font-semibold text-lg mb-2">How long does credit repair take?</h3>
        <p className="text-muted-foreground">
         Results vary, but most customers see improvements within 30-45 days after dispute letters are sent. Comprehensive credit repair may take 3-6 months.
        </p>
       </div>
       <div>
        <h3 className="font-semibold text-lg mb-2">Can I cancel my subscription?</h3>
        <p className="text-muted-foreground">
         Yes, you can cancel your subscription at any time from your account settings. There are no long-term contracts or cancellation fees.
        </p>
       </div>
       <div>
        <h3 className="font-semibold text-lg mb-2">Is there a guarantee?</h3>
        <p className="text-muted-foreground">
         We offer a 30-day money-back guarantee if you're not satisfied with our service. However, we cannot guarantee specific credit score increases as results vary by individual.
        </p>
       </div>
      </div>
     </div>
    </div>
   </div>
  );
}
