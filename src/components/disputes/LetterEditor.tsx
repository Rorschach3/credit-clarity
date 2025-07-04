
import React, { useEffect } from "react";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { ParsedTradeline } from "@/utils/tradelineParser";
import { generateDisputeLetter } from "./generateDisputeLetter";

interface LetterEditorProps {
  selectedTradelines: ParsedTradeline[];
  letter: string;
  setLetter: (letter: string) => void;
}

export const LetterEditor: React.FC<LetterEditorProps> = ({
  selectedTradelines,
  letter,
  setLetter
}) => {
  
  useEffect(() => {
    if (selectedTradelines.length > 0) {
      const defaultUserInfo = {
        firstName: "John",
        lastName: "Doe",
        address: "123 Main Street",
        city: "Anytown",
        state: "CA",
        zip: "12345",
        phoneNumber: "(555) 123-4567",
        emailAddress: "john.doe@email.com"
      };

      const defaultBureau = {
        name: "Experian",
        address: "P.O. Box 4500",
        city: "Allen",
        state: "TX",
        zip: "75013"
      };

      generateDisputeLetter(defaultUserInfo, selectedTradelines, defaultBureau)
        .then(generatedLetter => {
          setLetter(generatedLetter);
        })
        .catch(error => {
          console.error("Error generating letter:", error);
        });
    }
  }, [selectedTradelines, setLetter]);

  return (
    <div className="space-y-4">
      <div>
        <Label htmlFor="dispute-letter">Generated Dispute Letter</Label>
        <Textarea
          id="dispute-letter"
          value={letter}
          onChange={(e) => setLetter(e.target.value)}
          placeholder="Your dispute letter will be generated here based on selected tradelines..."
          className="min-h-[400px] font-mono text-sm"
        />
      </div>
      <p className="text-sm text-muted-foreground">
        You can edit the letter above to customize it for your specific situation.
        The letter is automatically generated based on your selected tradelines.
      </p>
    </div>
  );
};
