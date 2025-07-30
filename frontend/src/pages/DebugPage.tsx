import React from 'react';
import PDFDebugger from '@/components/debug/PDFDebugger';

const DebugPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-center mb-2">
            PDF Parsing Debug Tools
          </h1>
          <p className="text-muted-foreground text-center">
            Test and debug PDF parsing methods to understand why only some tradelines are extracted
          </p>
        </div>
        
        <PDFDebugger />
      </div>
    </div>
  );
};

export default DebugPage;