import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card } from "@/components/ui/card";
import { toast } from "sonner";
import { Mail, Phone, MapPin } from "lucide-react";

export default function ContactPage() {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    subject: "",
    message: ""
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    
    // Simulate form submission
    setTimeout(() => {
      toast.success("Your message has been sent! We'll get back to you soon.");
      setFormData({
        name: "",
        email: "",
        subject: "",
        message: ""
      });
      setIsSubmitting(false);
    }, 1500);
  };

  return (
    <div className="py-16 px-4 container">
     <div className="max-w-3xl mx-auto text-center mb-12">
      <h1 className="text-4xl font-bold mb-4">Contact Us</h1>
        <p className="text-xl text-gray-600">
          Have questions or need help? We're here for you.
        </p>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 max-w-5xl mx-auto">
        <div className="lg:col-span-2">
          <Card className="p-6">
            <h2 className="text-2xl font-semibold mb-6">Send Us a Message</h2>
            <form onSubmit={handleSubmit}>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
                <div className="space-y-2">
                  <Label htmlFor="name">Your Name</Label>
                  <Input 
                    id="name" 
                    name="name" 
                    value={formData.name}
                    onChange={handleChange}
                    placeholder="John Doe" 
                    required 
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="email">Email Address</Label>
                  <Input 
                    id="email" 
                    name="email"
                    type="email"
                    value={formData.email}
                    onChange={handleChange}
                    placeholder="john@example.com" 
                    required 
                  />
                </div>
              </div>
              
              <div className="space-y-2 mb-4">
                <Label htmlFor="subject">Subject</Label>
                <Input 
                  id="subject" 
                  name="subject"
                  value={formData.subject}
                  onChange={handleChange}
                  placeholder="How can we help you?" 
                  required 
                />
              </div>
              
              <div className="space-y-2 mb-6">
                <Label htmlFor="message">Message</Label>
                <Textarea 
                  id="message" 
                  name="message"
                  value={formData.message}
                  onChange={handleChange}
                  placeholder="Your message here..." 
                  rows={6}
                  required 
                />
              </div>
              
              <Button type="submit" disabled={isSubmitting} className="w-full">
                {isSubmitting ? "Sending..." : "Send Message"}
              </Button>
            </form>
          </Card>
        </div>
        
        <div>
          <Card className="p-6 mb-6">
            <h2 className="text-xl font-semibold mb-4">Contact Information</h2>
            <div className="space-y-4">
              <div className="flex items-start">
                <Mail className="h-5 w-5 text-brand-600 mt-1 mr-3" />
                <div>
                  <p className="font-medium">Email</p>
                  <a href="mailto:support@creditclarityai.com" className="text-brand-600 hover:underline">
                    support@creditclarityai.com
                  </a>
                </div>
              </div>
              
              <div className="flex items-start">
                <Phone className="h-5 w-5 text-brand-600 mt-1 mr-3" />
                <div>
                  <p className="font-medium">Phone</p>
                  <a href="tel:+18005551234" className="text-brand-600 hover:underline">
                    (800) 555-1234
                  </a>
                </div>
              </div>
              
              <div className="flex items-start">
                <MapPin className="h-5 w-5 text-brand-600 mt-1 mr-3" />
                <div>
                  <p className="font-medium">Address</p>
                  <p>
                    123 Credit Street<br />
                    Suite 456<br />
                    San Francisco, CA 94105
                  </p>
                </div>
              </div>
            </div>
          </Card>
          
          <Card className="p-6">
            <h2 className="text-xl font-semibold mb-4">Business Hours</h2>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span>Monday - Friday</span>
                <span>9:00 AM - 6:00 PM ET</span>
              </div>
              <div className="flex justify-between">
                <span>Saturday</span>
                <span>10:00 AM - 4:00 PM ET</span>
              </div>
              <div className="flex justify-between">
                <span>Sunday</span>
                <span>Closed</span>
              </div>
            </div>
          </Card>
        </div>
      </div>
      
      <div className="mt-12 max-w-3xl mx-auto text-center">
        <h2 className="text-2xl font-semibold mb-6">Frequently Asked Questions</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-left">
          <div>
            <h3 className="font-semibold text-lg mb-2">How quickly will you respond?</h3>
            <p className="text-gray-600">
              We typically respond to all inquiries within 24 business hours.
            </p>
          </div>
          <div>
            <h3 className="font-semibold text-lg mb-2">Do you offer phone support?</h3>
            <p className="text-gray-600">
              Yes, phone support is available for all customers during business hours.
            </p>
          </div>
          <div>
            <h3 className="font-semibold text-lg mb-2">Can I schedule a consultation?</h3>
            <p className="text-gray-600">
              Absolutely! Premium and Enterprise customers can schedule one-on-one consultations.
            </p>
          </div>
          <div>
            <h3 className="font-semibold text-lg mb-2">Do you have a physical office?</h3>
            <p className="text-gray-600">
              Yes, our headquarters is located in San Francisco, but most of our services are provided remotely.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
