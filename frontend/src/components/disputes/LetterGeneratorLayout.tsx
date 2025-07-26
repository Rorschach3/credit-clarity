import React from "react"
import { LetterGeneratorForm } from "./LetterGeneratorForm"
import { LetterPreview } from "./LetterPreview"
import { Card } from "../ui/card"

export function LetterGeneratorLayout() {
  // Since LetterGeneratorForm manages its own state internally and does not expose it,
  // we cannot connect it dynamically to LetterPreview without modifying internal logic.
  // Therefore, we arrange the components side by side for now.

  // Placeholder content for LetterPreview
  const placeholderContent = "Your formatted letter preview will appear here."

  return (
    <div className="flex flex-col h-full min-h-screen">
      {/* Navigation is included inside LetterGeneratorForm */}
      <div className="flex flex-1 flex-col md:flex-row gap-6 p-6 max-w-7xl mx-auto w-full">
        <div className="md:w-1/2">
          <Card className="h-full">
            <LetterGeneratorForm />
          </Card>
        </div>
        <div className="md:w-1/2">
          <Card className="h-full">
            <h2 className="text-lg font-semibold mb-4">Letter Preview</h2>
            <LetterPreview
              content={placeholderContent}
              fontSize="text-base"
              bold={false}
              italic={false}
              alignment="left"
            />
          </Card>
        </div>
      </div>
    </div>
  )
}