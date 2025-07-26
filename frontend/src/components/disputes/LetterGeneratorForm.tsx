import * as React from "react"
import { useState } from "react"
import { Input } from "../ui/input"
import { Label } from "../ui/label"
import { Textarea } from "../ui/textarea"
import { Toggle } from "../ui/toggle"
import { ToggleGroup } from "../ui/toggle-group"
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "../ui/select"
import { RadioGroup, RadioGroupItem } from "../ui/radio-group"
import { LetterGeneratorNav } from "./LetterGeneratorNav"

export function LetterGeneratorForm() {
  // State for letter content inputs
  const [recipient, setRecipient] = useState("")
  const [subject, setSubject] = useState("")
  const [body, setBody] = useState("")

  // State for formatting options
  const [fontSize, setFontSize] = useState("16")
  const [isBold, setIsBold] = useState(false)
  const [isItalic, setIsItalic] = useState(false)
  const [alignment, setAlignment] = useState("left")

  // Font size options
  const fontSizes = [
    { label: "12", value: "12" },
    { label: "14", value: "14" },
    { label: "16", value: "16" },
    { label: "18", value: "18" },
    { label: "20", value: "20" },
    { label: "24", value: "24" },
  ]

  return (
    <>
      <LetterGeneratorNav />
      <form className="space-y-6 p-4 max-w-lg mx-auto">
        {/* Recipient Name */}
        <div>
          <Label htmlFor="recipient">Recipient Name</Label>
          <Input
            id="recipient"
            type="text"
            placeholder="Enter recipient name"
            value={recipient}
            onChange={(e) => setRecipient(e.target.value)}
          />
        </div>

        {/* Subject */}
        <div>
          <Label htmlFor="subject">Subject</Label>
          <Input
            id="subject"
            type="text"
            placeholder="Enter subject"
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
          />
        </div>

        {/* Body Text */}
        <div>
          <Label htmlFor="body">Body Text</Label>
          <Textarea
            id="body"
            placeholder="Enter letter body"
            value={body}
            onChange={(e) => setBody(e.target.value)}
            rows={6}
          />
        </div>

        {/* Formatting Options */}
        <fieldset className="space-y-4">
          <legend className="text-sm font-medium">Formatting Options</legend>

          {/* Font Size */}
          <div>
            <Label htmlFor="font-size">Font Size</Label>
            <Select value={fontSize} onValueChange={setFontSize}>
              <SelectTrigger id="font-size" className="w-full">
                <SelectValue placeholder="Select font size" />
              </SelectTrigger>
              <SelectContent>
                {fontSizes.map((size) => (
                  <SelectItem key={size.value} value={size.value}>
                    {size.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Bold Toggle */}
          <div className="flex items-center space-x-4">
            <Toggle
              id="bold"
              pressed={isBold}
              onPressedChange={(pressed) => setIsBold(pressed)}
              aria-label="Toggle bold text"
            >
              Bold
            </Toggle>

            {/* Italic Toggle */}
            <Toggle
              id="italic"
              pressed={isItalic}
              onPressedChange={(pressed) => setIsItalic(pressed)}
              aria-label="Toggle italic text"
            >
              Italic
            </Toggle>
          </div>

          {/* Alignment Radio Group */}
          <div>
            <Label>Alignment</Label>
            <RadioGroup
              value={alignment}
              onValueChange={setAlignment}
              className="flex space-x-4"
              aria-label="Text alignment"
            >
              <RadioGroupItem value="left" id="align-left" />
              <Label htmlFor="align-left">Left</Label>

              <RadioGroupItem value="center" id="align-center" />
              <Label htmlFor="align-center">Center</Label>

              <RadioGroupItem value="right" id="align-right" />
              <Label htmlFor="align-right">Right</Label>
            </RadioGroup>
          </div>
        </fieldset>
      </form>
    </>
  )
}