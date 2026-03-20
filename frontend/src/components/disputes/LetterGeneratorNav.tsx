import * as React from "react"
import { Button } from "../ui/button"
import { useNavigate } from "react-router-dom"
import { useAuth } from "@/hooks/use-auth"

export function LetterGeneratorNav() {
  const navigate = useNavigate()
  const { logout } = useAuth()

  const handleLogout = async () => {
    try {
      await logout()
      navigate("/login")
    } catch (error) {
      console.error("Logout failed:", error)
    }
  }

  const handleProfile = () => {
    // Navigate to profile page
    navigate("/profile")
  }

  return (
    <nav className="flex justify-end space-x-4 p-4 border-b border-gray-200">
      <Button variant="outline" size="sm" onClick={handleProfile} aria-label="View Profile">
        Profile
      </Button>
      <Button variant="destructive" size="sm" onClick={handleLogout} aria-label="Logout">
        Logout
      </Button>
    </nav>
  )
}