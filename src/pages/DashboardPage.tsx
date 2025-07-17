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
