import React from "react"
import { Card } from "../ui/card"
import { ScrollArea } from "../ui/scroll-area"

export interface LetterPreviewProps {
  content: string
  fontSize?: string // Tailwind font size classes or CSS size (e.g. "text-base", "16px")
  bold?: boolean
  italic?: boolean
  alignment?: "left" | "center" | "right" | "justify"
}

export const LetterPreview: React.FC<LetterPreviewProps> = ({
  content,
  fontSize = "text-base",
  bold = false,
  italic = false,
  alignment = "left",
}) => {
  // Compose class names for font style and alignment
  const fontWeightClass = bold ? "font-bold" : "font-normal"
  const fontStyleClass = italic ? "italic" : "not-italic"
  const textAlignClass = (() => {
    switch (alignment) {
      case "center":
        return "text-center"
      case "right":
        return "text-right"
      case "justify":
        return "text-justify"
      case "left":
      default:
        return "text-left"
    }
  })()

  return (
    <Card className="max-h-[400px] p-4">
      <ScrollArea className="h-[380px]">
        <div
          className={`${fontSize} ${fontWeightClass} ${fontStyleClass} ${textAlignClass} whitespace-pre-wrap break-words`}
          style={{ whiteSpace: "pre-wrap" }}
          // Render content as plain text with preserved whitespace and line breaks
        >
          {content}
        </div>
      </ScrollArea>
    </Card>
  )
}