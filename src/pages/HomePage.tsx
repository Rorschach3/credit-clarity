import React from 'react';
import { Helmet } from "react-helmet";

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
        <meta property="og:image" content="https://creditclarity.com/og-image.jpg" />
      </Helmet>

      <header className="bg-gray-900 flex justify-center items-center border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex justify-between items-center h-16">
          <h1 className="text-5xl font-bold text-white">Credit Clarity AI Assist</h1>
        </div>
      </header>

      <main className="bg-gray-900 text-white min-h-screen">
        {/* Hero Section */}
        <section className="max-w-7xl mx-auto mb-8 px-4 sm:px-6 lg:px-8 py-16 text-center">
          <h2 className="text-4xl md:text-4xl font-extrabold mb-4">Take Control of Your Credit Score</h2>
          <p className="text-lg md:text-xl mb-4 max-w-3xl mx-auto">
            AI-powered platform to analyze, dispute, and improve your credit score with ease and confidence.
          </p>
          <a
            href="/signup"
            className="inline-block bg-blue-600 hover:bg-blue-700 text-white font-semibold px-8 py-3 rounded-lg m-4 text-lg transition"
            aria-label="Sign up now"
          >
            Get Started
          </a>
          <a
            href="/signup"
            className="inline-block bg-blue-600 hover:bg-blue-700 text-white font-semibold px-8 py-3 mb-20 rounded-lg text-lg transition"
            aria-label="Sign up for Credit Clarity AI Assist"
          >
            Sign Up Now
          </a>
          <div className="mx-auto mb-10 max-w-4xl flex justify-center items-center rounded-lg overflow-hidden shadow-lg">
            <img src="https://i.ibb.co/HD1HjjhN/031144832693.png" alt="Credit Clarity Logo" className="w-full max-w-md h-auto object-contain" />
          </div>

        </section>



        {/* Features Section */}
        <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
          <h3 className="text-3xl font-extrabold mb-12 text-center">How to Get Started</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-10 text-center">
            <div className="bg-gray-800 rounded-lg p-8 shadow-lg hover:shadow-xl transition">
              <div className="text-blue-500 mb-4 text-5xl font-bold">1</div>
              <h4 className="text-xl font-semibold mb-2">Sign Up</h4>
              <p>Create your free account to get personalized credit insights.</p>
            </div>
            <div className="bg-gray-800 rounded-lg p-8 shadow-lg hover:shadow-xl transition">
              <div className="text-blue-500 mb-4 text-5xl font-bold">2</div>
              <h4 className="text-xl font-semibold mb-2">Analyze</h4>
              <p>Upload your credit reports and let AI analyze your credit profile.</p>
            </div>
            <div className="bg-gray-800 rounded-lg p-8 shadow-lg hover:shadow-xl transition">
              <div className="text-blue-500 mb-4 text-5xl font-bold">3</div>
              <h4 className="text-xl font-semibold mb-2">Dispute & Improve</h4>
              <p>Generate dispute letters and track your credit score improvements.</p>
            </div>
          </div>
        </section>
      </main>
    </>
  );
});

export default HomePage;
