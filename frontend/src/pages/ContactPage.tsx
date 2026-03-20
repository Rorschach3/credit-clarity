import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "sonner";
import { Mail, Phone, MapPin, Clock } from "lucide-react";
import { Helmet } from "react-helmet-async";

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

    setTimeout(() => {
      toast.success("Your message has been sent! We'll get back to you soon.");
      setFormData({ name: "", email: "", subject: "", message: "" });
      setIsSubmitting(false);
    }, 1500);
  };

  return (
    <>
      <Helmet>
        <title>Contact Us - Credit Clarity | Get Expert Credit Repair Help</title>
        <meta name="description" content="Have questions about credit repair? Contact Credit Clarity for expert support. We're here to help you improve your credit score with AI-powered solutions." />
        <meta name="keywords" content="contact credit repair, credit repair support, credit clarity contact, credit score help" />
        <meta property="og:title" content="Contact Us - Credit Clarity" />
        <meta property="og:description" content="Have questions about credit repair? Contact Credit Clarity for expert support." />
        <meta property="og:type" content="website" />
        <meta name="twitter:card" content="summary_large_image" />
        <meta name="twitter:title" content="Contact Us - Credit Clarity" />
        <meta name="twitter:description" content="Have questions about credit repair? Contact Credit Clarity for expert support." />
        <link rel="canonical" href="https://creditclarity.ai/contact" />
      </Helmet>

      <div className="has-navbar">

        {/* Header */}
        <section className="relative overflow-hidden px-6 pt-24 pb-16 md:pt-32 md:pb-20">
          <div
            className="absolute inset-0 pointer-events-none"
            style={{
              background: 'radial-gradient(ellipse 80% 60% at 50% -10%, rgba(212,168,83,0.10) 0%, transparent 70%)',
            }}
          />
          <div className="relative max-w-3xl mx-auto text-center">
            <h1 className="text-5xl md:text-6xl font-extrabold mb-4" style={{ letterSpacing: '-0.03em' }}>
              <span className="text-gold-gradient">Contact</span> Us
            </h1>
            <p className="text-muted-foreground text-lg">
              Have questions or need help? We're here for you.
            </p>
          </div>
        </section>

        {/* Main grid */}
        <section className="px-6 pb-24 max-w-5xl mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

            {/* Form */}
            <div className="lg:col-span-2 card-midnight rounded-xl p-8">
              <h2 className="text-xl font-semibold mb-6">Send Us a Message</h2>
              <form onSubmit={handleSubmit} className="space-y-5">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
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

                <div className="space-y-2">
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

                <div className="space-y-2">
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

                <Button type="submit" disabled={isSubmitting} className="btn-gold w-full rounded-md h-11">
                  {isSubmitting ? "Sending..." : "Send Message"}
                </Button>
              </form>
            </div>

            {/* Sidebar */}
            <div className="flex flex-col gap-6">
              <div className="card-midnight rounded-xl p-6">
                <h2 className="text-lg font-semibold mb-5">Contact Information</h2>
                <div className="space-y-5">
                  <div className="flex items-start gap-3">
                    <div className="p-2 rounded-lg bg-[rgba(212,168,83,0.1)] flex-shrink-0">
                      <Mail className="h-4 w-4 text-[#D4A853]" />
                    </div>
                    <div>
                      <p className="text-sm font-medium mb-0.5">Email</p>
                      <a href="mailto:support@creditclarityai.com" className="text-sm text-[#D4A853] hover:text-[#E8C06A] transition-colors">
                        support@creditclarityai.com
                      </a>
                    </div>
                  </div>

                  <div className="flex items-start gap-3">
                    <div className="p-2 rounded-lg bg-[rgba(212,168,83,0.1)] flex-shrink-0">
                      <Phone className="h-4 w-4 text-[#D4A853]" />
                    </div>
                    <div>
                      <p className="text-sm font-medium mb-0.5">Phone</p>
                      <a href="tel:+18005551234" className="text-sm text-[#D4A853] hover:text-[#E8C06A] transition-colors">
                        (800) 555-1234
                      </a>
                    </div>
                  </div>

                  <div className="flex items-start gap-3">
                    <div className="p-2 rounded-lg bg-[rgba(212,168,83,0.1)] flex-shrink-0">
                      <MapPin className="h-4 w-4 text-[#D4A853]" />
                    </div>
                    <div>
                      <p className="text-sm font-medium mb-0.5">Address</p>
                      <p className="text-sm text-muted-foreground">
                        123 Credit Street, Suite 456<br />
                        San Francisco, CA 94105
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              <div className="card-midnight rounded-xl p-6">
                <div className="flex items-center gap-2 mb-5">
                  <Clock className="h-4 w-4 text-[#D4A853]" />
                  <h2 className="text-lg font-semibold">Business Hours</h2>
                </div>
                <div className="space-y-2 text-sm">
                  {[
                    { day: 'Monday – Friday', hours: '9:00 AM – 6:00 PM ET' },
                    { day: 'Saturday', hours: '10:00 AM – 4:00 PM ET' },
                    { day: 'Sunday', hours: 'Closed' },
                  ].map(({ day, hours }) => (
                    <div key={day} className="flex justify-between">
                      <span className="text-muted-foreground">{day}</span>
                      <span className={hours === 'Closed' ? 'text-muted-foreground' : 'text-foreground font-medium'}>{hours}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* FAQ mini-section */}
          <div className="mt-16">
            <h2 className="text-2xl font-bold mb-8 text-center" style={{ letterSpacing: '-0.02em' }}>
              Quick Answers
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              {[
                {
                  q: 'How quickly will you respond?',
                  a: 'We typically respond to all inquiries within 24 business hours.',
                },
                {
                  q: 'Do you offer phone support?',
                  a: 'Yes, phone support is available for all customers during business hours.',
                },
                {
                  q: 'Can I schedule a consultation?',
                  a: 'Absolutely! Premium and Enterprise customers can schedule one-on-one consultations.',
                },
                {
                  q: 'Do you have a physical office?',
                  a: 'Yes, our headquarters is in San Francisco, but most services are provided remotely.',
                },
              ].map(({ q, a }) => (
                <div key={q} className="card-midnight rounded-xl p-6">
                  <h3 className="font-semibold mb-2">{q}</h3>
                  <p className="text-sm text-muted-foreground leading-relaxed">{a}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

      </div>
    </>
  );
}
