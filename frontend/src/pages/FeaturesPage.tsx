
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Check, FileText, Bot, ShieldCheck, TrendingUp } from "lucide-react";

export default function FeaturesPage() {
  return (
    <div className="container mx-auto py-12">
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold mb-4">Features</h1>
        <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
          Our comprehensive credit repair platform provides everything you need to improve your credit score
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-16">
        <FeatureCard
          title="AI-Powered Credit Report Analysis"
          description="Our advanced AI analyzes your credit reports to identify errors, inconsistencies, and items with high dispute potential."
          icon={<Bot className="h-8 w-8 text-primary" />}
          badges={["AI Technology", "Smart Detection"]}
        />
        
        <FeatureCard
          title="Customized Dispute Letters"
          description="Generate professionally written dispute letters tailored to your specific credit issues and circumstances."
          icon={<FileText className="h-8 w-8 text-primary" />}
          badges={["Professional Templates", "Bureau-Specific"]}
        />
        
        <FeatureCard
          title="Comprehensive Credit Monitoring"
          description="Track your credit score progress and receive alerts about changes to your credit report."
          icon={<TrendingUp className="h-8 w-8 text-primary" />}
          badges={["Real-time Alerts", "Score Tracking"]}
        />
        
        <FeatureCard
          title="Identity Protection"
          description="Advanced security features to protect your personal information during the dispute process."
          icon={<ShieldCheck className="h-8 w-8 text-primary" />}
          badges={["Secure Encryption", "Data Protection"]}
        />
      </div>

      <div className="bg-primary/5 rounded-lg p-8 mb-16">
        <h2 className="text-2xl font-bold mb-4 text-center">How Our Platform Works</h2>
        
        <div className="grid gap-8 md:grid-cols-3">
          <ProcessStep
            number={1}
            title="Upload Your Credit Reports"
            description="Submit your credit reports from all three major bureaus or manually enter account information."
          />
          
          <ProcessStep
            number={2}
            title="AI Analysis & Selection"
            description="Our AI identifies items with high dispute potential, and you select which ones to challenge."
          />
          
          <ProcessStep
            number={3}
            title="Generate & Send Letters"
            description="Custom dispute letters are generated for each bureau, ready for you to print and mail."
          />
        </div>
      </div>

      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold">Ready to Improve Your Credit Score?</h2>
        <p className="text-muted-foreground mt-2 mb-6">
          Start your credit repair journey today with our AI-powered platform
        </p>
        <a 
          href="/signup" 
          className="bg-primary text-primary-foreground hover:bg-primary/90 px-8 py-3 rounded-md font-medium"
        >
          Get Started
        </a>
      </div>
    </div>
  );
}

interface FeatureCardProps {
  title: string;
  description: string;
  icon: React.ReactNode;
  badges: string[];
}

function FeatureCard({ title, description, icon, badges }: FeatureCardProps) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center gap-4">
        <div className="bg-primary/10 p-3 rounded-full">{icon}</div>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-muted-foreground mb-4">{description}</p>
        <div className="flex flex-wrap gap-2">
          {badges.map((badge) => (
            <Badge key={badge} variant="secondary">
              {badge}
            </Badge>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

interface ProcessStepProps {
  number: number;
  title: string;
  description: string;
}

function ProcessStep({ number, title, description }: ProcessStepProps) {
  return (
    <div className="flex flex-col items-center text-center">
      <div className="bg-primary text-primary-foreground rounded-full w-12 h-12 flex items-center justify-center font-bold text-lg mb-4">
        {number}
      </div>
      <h3 className="font-semibold text-lg mb-2">{title}</h3>
      <p className="text-muted-foreground">{description}</p>
    </div>
  );
}
