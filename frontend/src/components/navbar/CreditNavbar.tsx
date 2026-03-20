import { useNavigate } from 'react-router-dom';
import { useState } from 'react';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Menu, X } from 'lucide-react';

export function CreditNavbar() {
  const navigate = useNavigate();
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <header className="sticky top-0 z-20 bg-background/90 backdrop-blur-sm border-b border-border">
      <div className="max-w-6xl mx-auto flex items-center justify-between px-4 py-2">
        {/* left spacer or logo could go here */}
        <div />
        <button
          className="sm:hidden p-2 text-foreground"
          aria-label="Toggle menu"
          onClick={() => setMobileOpen(o => !o)}
        >
          {mobileOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
        </button>
      </div>
      <div
        className={`overflow-hidden transition-[max-height] duration-300 ease-in-out w-full ${
          mobileOpen ? 'max-h-screen' : 'max-h-0'
        } sm:max-h-full`}
      >
        <div className="bg-gradient-to-r from-primary to-secondary p-[1px]">
          <Tabs defaultValue="overview">
            <TabsList className="bg-[#1e2235] rounded-md flex flex-wrap gap-2 p-2 mb-6">
              <TabsTrigger value="/src/pages/DashboardPage.tsx" onClick={() => navigate('/Dashboard')}>Overview</TabsTrigger>
              <TabsTrigger value="/src/pages/CreditReportUploadPage.tsx" onClick={() => navigate('/Credit-Report-Upload')}>Upload Credit Reports</TabsTrigger>
              <TabsTrigger value="/src/pages/NegativeTradelinesPage.tsx" onClick={() => navigate('/Tradelines')}>Tradelines</TabsTrigger>
              <TabsTrigger value="/src/components/disputes/DisputeLetterGenerator.tsx" onClick={() => navigate('/dispute-wizard')}>Dispute Letter Generator</TabsTrigger>
            </TabsList>
          </Tabs>
        </div>
      </div>
    </header>
  );
}

        
