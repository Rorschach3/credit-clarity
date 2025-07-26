<<<<<<< Updated upstream:src/pages/DashboardPage.tsx
import MainLayout from "@/components/layout/MainLayout"
import { Navbar } from "../components/layout/Navbar"
import { Overview } from "../components/dashboard/Overview"
import { RecentActivity } from "../components/dashboard/RecentActivity"
import { DisputeSummary } from "../components/dashboard/DisputeSummary"
import { CreditScoreCard } from "../components/dashboard/CreditScoreCard"
import { useAuth } from "@/hooks/use-auth"
import { useState } from "react"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { useNavigate } from "react-router-dom"

const Dashboard = () => {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [scores, setScores] = useState({
    experian: null,
    transunion: null,
    equifax: null,
  })

  return (
   <MainLayout>
    <div className="min-h-screen bg-[#0f111a] text-white flex flex-col">

      <main className="flex-grow max-w-7xl mx-auto px-6 md:px-8 py-10 space-y-8">
        <div>
          <h1 className="text-4xl font-bold mb-6">Your Credit Dashboard</h1>

        <Tabs defaultValue="overview">
          <TabsList className="bg-[#1e2235] rounded-md flex flex-wrap gap-2 p-2 mb-6">
            <TabsTrigger value="overview" onClick={() => navigate('/dashboard')}>Overview</TabsTrigger>
            <TabsTrigger value="disputes" onClick={() => navigate('/disputes')}>Disputes</TabsTrigger>
            <TabsTrigger value="tradelines" onClick={() => navigate('/tradelines')}>Tradelines</TabsTrigger>
            <TabsTrigger value="dispute-generator" onClick={() => navigate('/dispute-wizard')}>Dispute Letter Generator</TabsTrigger>
          </TabsList>
        </Tabs>

        </div>

        <section className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <CreditScoreCard
            bureau="Experian"
            score={scores.experian?.score ?? 645}
            lastUpdated="14 days ago"
            change={12}
          />
          <CreditScoreCard
            bureau="TransUnion"
            score={scores.transunion?.score ?? 658}
            lastUpdated="14 days ago"
            change={8}
          />
          <CreditScoreCard
            bureau="Equifax"
            score={scores.equifax?.score ?? 672}
            lastUpdated="14 days ago"
            change={15}
          />
        </section>

        <section className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <RecentActivity />
          <DisputeSummary />
        </section>
      </main>

      <footer className="bg-[#1f1f1f] py-10 text-sm text-gray-400 mt-10">
        <div className="max-w-7xl mx-auto px-6 md:px-8 grid grid-cols-1 md:grid-cols-3 gap-8">
          <div>
            <p className="mb-4 leading-relaxed">
              Helping you improve your credit score through AI-powered credit report analysis and dispute letter generation.
            </p>
            <div className="flex space-x-4">
              <a href="#" aria-label="Twitter" className="hover:text-white">🐦</a>
              <a href="#" aria-label="LinkedIn" className="hover:text-white">💼</a>
              <a href="#" aria-label="Facebook" className="hover:text-white">📘</a>
            </div>
          </div>

          <div>
            <h4 className="text-white font-semibold mb-3">Product</h4>
            <ul className="space-y-2">
              <li><a href="#" className="hover:text-white">Pricing</a></li>
              <li><a href="#" className="hover:text-white">Features</a></li>
              <li><a href="#" className="hover:text-white">Testimonials</a></li>
              <li><a href="#" className="hover:text-white">FAQ</a></li>
            </ul>
          </div>

          <div>
            <h4 className="text-white font-semibold mb-3">Company</h4>
            <ul className="space-y-2">
              <li><a href="#" className="hover:text-white">About Us</a></li>
              <li><a href="#" className="hover:text-white">Contact</a></li>
              <li><a href="#" className="hover:text-white">Privacy Policy</a></li>
              <li><a href="#" className="hover:text-white">Terms of Service</a></li>
            </ul>
          </div>
        </div>
      </footer>
    </div>
   </MainLayout>
  )
}

export default Dashboard
=======
// src/pages/DashboardPage.tsx

import { useAuth } from "@/hooks/use-auth"
import { CreditNavbar } from "@/components/navbar/CreditNavbar"
import CreditDashboard from "@/components/dashboard/CreditDashboard"

const Dashboard = () => {
  useAuth()

  return (
    <div className="min-h-screen bg-background text-foreground">
      <CreditNavbar />
      <CreditDashboard />
    </div>
  )
}

export default Dashboard
>>>>>>> Stashed changes:frontend/src/pages/DashboardPage.tsx
