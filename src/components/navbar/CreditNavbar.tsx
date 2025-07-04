import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';

export function CreditNavbar() {
  const navigate = useNavigate();

          return (
            <header className="bg-background border-b">
                <div>
                <Tabs defaultValue="overview">
                    <TabsList className="bg-[#1e2235] rounded-md flex flex-wrap gap-2 p-2 mb-6">
                    <TabsTrigger value="/src/pages/DashboardPage.tsx" onClick={() => navigate('/Dashboard')}>Overview</TabsTrigger>
                    <TabsTrigger value="/src/pages/CreditReportUploadPage.tsx" onClick={() => navigate('/Credit-Report-Upload')}>Upload Credit Reports</TabsTrigger>
                    <TabsTrigger value="/src/pages/NegativeTradelinesPage.tsx" onClick={() => navigate('/Tradelines')}>Tradelines</TabsTrigger>
                    <TabsTrigger value="/src/components/disputes/DisputeLetterGenerator.tsx" onClick={() => navigate('/dispute-wizard')}>Dispute Letter Generator</TabsTrigger>
                    </TabsList>
                </Tabs>
                </div>
            </header>
          );
        }
        
        
