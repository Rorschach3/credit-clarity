import { Button } from "@/components/ui/button";
import { Link } from "react-router-dom";
import { Shield, UserCheck, BookOpen } from "lucide-react";

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
      <div className="bg-gradient-to-r from-brand-900 to-brand-700 text-white py-20">
        {/* Hero Section */}
        <div className="container px-4 mx-auto">
          <div className="max-w-3xl mx-auto text-center">
            <h1 className="text-4xl font-bold mb-6">About Credit Clarity</h1>
            <p className="text-xl text-gray-700 mb-8">
              We're on a mission to help millions of Americans improve their credit scores through the power of artificial intelligence.
            </p>
            <div className="flex justify-center space-x-4">
              <Link to="/signup">
                <Button>Get Started</Button>
              </Link>
              <Link to="/contact">
                <Button variant="outline">Contact Us</Button>
              </Link>
            </div>
          </div>
        </div>
      </div>

      <section className="py-16">
      <div className="container px-4 mx-auto mt-12">
        {/* Our Story Section */}
        <div className="container px-4 mx-auto">
          <div className="max-w-3xl mx-auto">
            <h2 className="text-3xl font-bold mb-6 text-center">Our Story</h2>
            <div className="prose prose-lg max-w-none">
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
          </div>
        </div>
      </div>
      </section>

      {/* Our Values Section */}
      <section className="py-16 bg-gray-50">
        <div className="container px-4 mx-auto">
          <div className="max-w-3xl mx-auto text-center mb-12">
            <h2 className="text-3xl font-bold mb-4">Our Core Values</h2>
            <p className="text-lg text-gray-600">
              The principles that guide everything we do
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-5xl mx-auto">
            <div className="bg-white p-6 rounded-lg shadow-sm text-center">
              <div className="bg-brand-100 w-14 h-14 rounded-full flex items-center justify-center mx-auto mb-4">
                <Shield className="h-7 w-7 text-brand-600" />
              </div>
              <h3 className="text-xl font-semibold mb-2">Transparency</h3>
              <p className="text-gray-600">
                We're honest and upfront about what our service can and cannot do, with fair pricing and no hidden fees.
              </p>
            </div>
            
            <div className="bg-white p-6 rounded-lg shadow-sm text-center">
              <div className="bg-brand-100 w-14 h-14 rounded-full flex items-center justify-center mx-auto mb-4">
                <BookOpen className="h-7 w-7 text-brand-600" />
              </div>
              <h3 className="text-xl font-semibold mb-2">Education</h3>
              <p className="text-gray-600">
                We believe in empowering our customers with knowledge about credit repair, scoring, and financial literacy.
              </p>
            </div>
            
            <div className="bg-white p-6 rounded-lg shadow-sm text-center">
              <div className="bg-brand-100 w-14 h-14 rounded-full flex items-center justify-center mx-auto mb-4">
                <UserCheck className="h-7 w-7 text-brand-600" />
              </div>
              <h3 className="text-xl font-semibold mb-2">Customer Success</h3>
              <p className="text-gray-600">
                We measure our success by the improvements in our customers' credit scores and financial opportunities.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-16">
        <div className="container px-4 mx-auto">
          <div className="max-w-5xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-8 text-center">
            <div>
              <p className="text-5xl font-bold text-brand-600 mb-2">15,000+</p>
              <p className="text-lg text-gray-600">Customers Served</p>
            </div>
            <div>
              <p className="text-5xl font-bold text-brand-600 mb-2">85%</p>
              <p className="text-lg text-gray-600">Success Rate</p>
            </div>
            <div>
              <p className="text-5xl font-bold text-brand-600 mb-2">68</p>
              <p className="text-lg text-gray-600">Average Score Increase</p>
            </div>
          </div>
        </div>
      </section>

      {/* Team Section */}
      <section className="py-16 bg-gray-50">
        <div className="container px-4 mx-auto">
          <div className="max-w-3xl mx-auto text-center mb-12">
            <h2 className="text-3xl font-bold mb-4">Our Team</h2>
            <p className="text-lg text-gray-600">
              Meet the experts behind CreditClarityAI
            </p>
          </div>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8 max-w-5xl mx-auto">
            {teamMembers.map((member, index) => (
              <div key={index} className="text-center">
                <div className="mb-4">
                  <img 
                    src={member.image} 
                    alt={member.name} 
                    className="w-32 h-32 rounded-full mx-auto object-cover"
                  />
                </div>
                <h3 className="text-lg font-semibold mb-1">{member.name}</h3>
                <p className="text-gray-600">{member.title}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-16 bg-brand-900 text-white">
        <div className="container px-4 mx-auto">
          <div className="max-w-3xl mx-auto text-center">
            <h2 className="text-3xl font-bold mb-4">Ready to Improve Your Credit?</h2>
            <p className="text-xl mb-8">
              Join thousands of customers who have successfully improved their credit scores with CreditClarityAI.
            </p>
            <Link to="/signup">
              <Button size="lg" className="bg-white text-brand-900 hover:bg-gray-100">
                Get Started Today
              </Button>
            </Link>
          </div>
        </div>
      </section>
    </>
  );
}
