import React, { useState, useEffect } from "react";
import { UserInfoForm } from "./UserInfoForm";
import { LetterEditor } from "./LetterEditor";
import { GenerateLettersSection } from "./GenerateLettersSection";
import { ParsedTradeline } from "@/utils/tradelineParser";
import { NegativeItem } from "@/types/document";
import { Button } from "@/components/ui/button";

interface UserInfo {
  name: string;
  address: string;
  city: string;
  state: string;
  zip: string;
}

interface DisputeWizardStep3DisputeLetterProps {
  userInfo: UserInfo;
  setUserInfo: (info: UserInfo) => void;
  selectedTradelines: ParsedTradeline[];
  letter: string;
  setLetter: (val: string) => void;
  onNext: () => void;
  onBack: () => void;
}

export const DisputeWizardStep3DisputeLetter: React.FC<DisputeWizardStep3DisputeLetterProps> = ({
  userInfo,
  setUserInfo,
  selectedTradelines,
  letter,
  setLetter,
  onNext,
  onBack,
}) => {
  // Convert selectedTradelines to NegativeItem[] for GenerateLettersSection
  // Assuming NegativeItem has similar structure to ParsedTradeline or adapt as needed
  const selectedItems: NegativeItem[] = selectedTradelines.map((tradeline) => ({
    id: tradeline.id || "",
    creditorName: tradeline.creditorName,
    accountNumber: tradeline.accountNumber,
    amount: tradeline.balance ? tradeline.balance.toString() : "", // Convert balance to string
    dateReported: "", // Provide a default empty string for dateReported
    bureaus: [], // Provide a default empty array for bureaus
    reason: "", // Provide a default empty string for reason
    status: tradeline.status,
  }));

  const [showDocsSection, setShowDocsSection] = useState(false);
  const [letterGenerated, setLetterGenerated] = useState(false);

  // Callback when letter generation completes
  const handleGenerationComplete = () => {
    setLetterGenerated(true);
  };

  // Optionally, update letter state when generation completes
  // The EnhancedDisputeLetterGenerator inside GenerateLettersSection should update letter via props or callbacks
  // Here we assume letter is updated externally; if not, we may need to add a callback to update letter

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <h2 className="text-2xl font-semibold">Step 3: Generate Dispute Letter</h2>

      <section>
        <h3 className="text-lg font-medium mb-2">Your Information</h3>
        <UserInfoForm userInfo={userInfo} onChange={setUserInfo} />
      </section>

      <section>
        <h3 className="text-lg font-medium mb-2">Generate Letter</h3>
        <GenerateLettersSection
          selectedItems={selectedItems}
          personalInfo={userInfo}
          onComplete={handleGenerationComplete}
          onBackToDocuments={() => setShowDocsSection(true)}
          onBackToItems={onBack}
        />
      </section>

      {letterGenerated && (
        <section>
          <h3 className="text-lg font-medium mb-2">Edit Letter</h3>
          <LetterEditor
            userInfo={userInfo}
            selectedTradelines={selectedTradelines}
            letter={letter}
            setLetter={setLetter}
            setShowDocsSection={setShowDocsSection}
          />
        </section>
      )}

      <div className="flex justify-between mt-6">
        <Button variant="outline" onClick={onBack}>
          Back
        </Button>
        <Button onClick={onNext} disabled={!letterGenerated}>
          Next
        </Button>
      </div>
    </div>
  );
};