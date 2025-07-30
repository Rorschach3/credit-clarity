import * as React from "react"
import { Button } from "../ui/button"
import { useNavigate } from "react-router-dom"

export function LetterGeneratorNav() {
  const navigate = useNavigate()

  const handleLogout = () => {
    // Placeholder logout logic
    // TODO: Replace with actual logout implementation
    console.log("Logout clicked")
    // For example, clear auth tokens and redirect to login page
    navigate("/login")
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