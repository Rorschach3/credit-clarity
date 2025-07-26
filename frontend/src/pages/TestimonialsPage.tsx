
import { Card, CardContent } from "@/components/ui/card";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { StarIcon } from "lucide-react";

export default function TestimonialsPage() {
  return (
    <div className="container mx-auto py-12">
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold mb-4">Customer Success Stories</h1>
        <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
          See how our AI-powered credit repair platform has helped customers improve their credit scores
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-16">
        <TestimonialCard
          name="Sarah Johnson"
          location="Denver, CO"
          rating={5}
          quote="After struggling with incorrect items on my credit report for months, this platform helped me identify and dispute them all. My score increased by 87 points in just two months!"
          imagePath="/placeholder.svg"
          initials="SJ"
        />
        
        <TestimonialCard
          name="Marcus Chen"
          location="Seattle, WA"
          rating={5}
          quote="The AI analysis was incredibly accurate. It found errors I'd never have caught on my own. The dispute letters were professional and effective - 3 collection accounts removed!"
          imagePath="/placeholder.svg"
          initials="MC"
        />
        
        <TestimonialCard
          name="Emily Rodriguez"
          location="Miami, FL"
          rating={4}
          quote="I was skeptical at first, but the results speak for themselves. The platform made the whole process so much easier than I expected. My credit score went up 65 points!"
          imagePath="/placeholder.svg"
          initials="ER"
        />
        
        <TestimonialCard
          name="David Thompson"
          location="Chicago, IL"
          rating={5}
          quote="The dispute letters this system generated were perfect. All four incorrect items were removed within 30 days. I couldn't be happier with the results."
          imagePath="/placeholder.svg"
          initials="DT"
        />
        
        <TestimonialCard
          name="Aisha Patel"
          location="Austin, TX"
          rating={5}
          quote="I was able to qualify for a mortgage after using this platform for just three months. The improvement in my credit score made all the difference."
          imagePath="/placeholder.svg"
          initials="AP"
        />
        
        <TestimonialCard
          name="Michael Wilson"
          location="Portland, OR"
          rating={4}
          quote="The step-by-step guidance made credit repair so much less intimidating. I'm now confident in managing my credit and have seen a 70 point increase!"
          imagePath="/placeholder.svg"
          initials="MW"
        />
      </div>

      <div className="bg-primary/5 rounded-lg p-8 text-center">
        <h2 className="text-2xl font-bold mb-4">Ready to Join Our Success Stories?</h2>
        <p className="text-muted-foreground mb-6 max-w-2xl mx-auto">
          Our AI-powered platform has helped thousands improve their credit scores. Start your journey today.
        </p>
        <div className="flex justify-center gap-4">
          <a 
            href="/signup" 
            className="bg-primary text-primary-foreground hover:bg-primary/90 px-6 py-2 rounded-md font-medium"
          >
            Sign Up Now
          </a>
          <a 
            href="/features" 
            className="border border-input bg-background hover:bg-accent hover:text-accent-foreground px-6 py-2 rounded-md font-medium"
          >
            Learn More
          </a>
        </div>
      </div>
    </div>
  );
}

interface TestimonialCardProps {
  name: string;
  location: string;
  rating: number;
  quote: string;
  imagePath: string;
  initials: string;
}

function TestimonialCard({ name, location, rating, quote, imagePath, initials }: TestimonialCardProps) {
  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-center gap-2 mb-2">
          {Array.from({ length: 5 }).map((_, i) => (
            <StarIcon 
              key={i} 
              className={`h-4 w-4 ${i < rating ? 'text-yellow-500 fill-yellow-500' : 'text-gray-300'}`} 
            />
          ))}
        </div>
        
        <blockquote className="text-muted-foreground mb-4">
          "{quote}"
        </blockquote>
        
        <div className="flex items-center gap-3">
          <Avatar>
            <AvatarImage src={imagePath} alt={name} />
            <AvatarFallback>{initials}</AvatarFallback>
          </Avatar>
          <div>
            <p className="font-medium">{name}</p>
            <p className="text-sm text-muted-foreground">{location}</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
