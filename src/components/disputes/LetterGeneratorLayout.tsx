import { useState } from "react";
import { LetterGeneratorForm } from "./LetterGeneratorForm";
import { LetterPreview } from "./LetterPreview";

interface LetterGeneratorLayoutProps {
  selectedItems?: any[];
}

export function LetterGeneratorLayout({ selectedItems = [] }: LetterGeneratorLayoutProps) {
  const [generatedLetter, setGeneratedLetter] = useState<string>("");

  const handleGenerate = (formData: any) => {
    // Generate letter logic here
    setGeneratedLetter("Generated letter content...");
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
      <div>
        <LetterGeneratorForm selectedItems={selectedItems} onGenerate={handleGenerate} />
      </div>
      <div>
        <LetterPreview letter={generatedLetter} />
      </div>
    </div>
  );
}
