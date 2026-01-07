import { Helmet } from "react-helmet-async";

export function OrganizationSchema() {
  const schema = {
    "@context": "https://schema.org",
    "@type": "Organization",
    "name": "Credit Clarity",
    "alternateName": "CreditClarityAI",
    "url": "https://creditclarity.ai",
    "logo": "https://creditclarity.ai/logo.png",
    "description": "AI-powered credit repair platform that helps Americans improve their credit scores through automated credit report analysis and dispute letter generation.",
    "email": "support@creditclarity.ai",
    "telephone": "+1-800-555-1234",
    "address": {
      "@type": "PostalAddress",
      "streetAddress": "123 Credit Street, Suite 456",
      "addressLocality": "San Francisco",
      "addressRegion": "CA",
      "postalCode": "94105",
      "addressCountry": "US"
    },
    "sameAs": [
      "https://twitter.com/creditclarity",
      "https://facebook.com/creditclarity",
      "https://linkedin.com/company/creditclarity"
    ],
    "foundingDate": "2024",
    "founders": [
      {
        "@type": "Person",
        "name": "Jane Cooper"
      }
    ],
    "numberOfEmployees": {
      "@type": "QuantitativeValue",
      "value": 15
    },
    "areaServed": {
      "@type": "Country",
      "name": "United States"
    },
    "serviceType": [
      "Credit Repair",
      "Credit Report Analysis",
      "Dispute Letter Generation",
      "Credit Score Improvement"
    ],
    "offers": {
      "@type": "AggregateOffer",
      "priceCurrency": "USD",
      "lowPrice": "0",
      "highPrice": "99",
      "offerCount": "3"
    }
  };

  return (
    <Helmet>
      <script type="application/ld+json">
        {JSON.stringify(schema)}
      </script>
    </Helmet>
  );
}
