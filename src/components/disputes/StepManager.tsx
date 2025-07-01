
import { useState } from "react";
import { EnhancedDocumentScanner } from "@/components/document/EnhancedDocumentScanner";
import { type NegativeItem } from "@/types/negative-item";
import { EnhancedNegativeItemsList } from "@/components/disputes/EnhancedNegativeItemsList";
import { useToast } from "@/hooks/use-toast";
import { DisputeAnalysis } from "@/utils/ai-service";
import { ManualDisputeForm } from "@/components/disputes/ManualDisputeForm";
import { PersonalInfoForm } from "@/components/disputes/PersonalInfoForm";
import { UserDocumentsSection } from "@/components/disputes/UserDocumentsSection";
import { SkipDocumentsAlert } from "@/components/disputes/SkipDocumentsAlert";
import { InputMethodTabs } from "@/components/disputes/InputMethodTabs";
import { CompletionStep } from "@/components/disputes/CompletionStep";
import { GenerateLettersSection } from "@/components/disputes/GenerateLettersSection";

type Step = 'personal' | 'scan' | 'select' | 'documents' | 'generate' | 'complete';

interface PersonalInfo {
  firstName: string
  lastName: string
  address: string
  city: string
  state: string
  zip: string
  phone?: string
  email: string
  ssnLastFour?: string
}

interface StepManagerProps {
  steps: {
    id: string;
    title: string;
    description: string;
    icon: React.ReactNode;
  }[];
  onStepChange: (step: Step) => void;
  onReset: () => void;
  personalInfo: PersonalInfo;
  setPersonalInfo: (info: PersonalInfo) => void;
  initialSelectedItems?: NegativeItem[];
}

export function StepManager({
  onStepChange,
  onReset,
  personalInfo,
  setPersonalInfo,
  initialSelectedItems = [],
}: StepManagerProps) {
  const [step, setStep] = useState<Step>('personal');
  const [negativeItems, setNegativeItems] = useState<NegativeItem[]>([]);
  const [selectedItems, setSelectedItems] = useState<NegativeItem[]>(initialSelectedItems);
  const [disputeAnalysis, setDisputeAnalysis] = useState<DisputeAnalysis | undefined>(undefined);
  const [entryMethod, setEntryMethod] = useState<'scan' | 'manual'>('scan');
  const { toast } = useToast();

  const handleScanComplete = (items: NegativeItem[], analysis?: DisputeAnalysis) => {
    setNegativeItems(items);
    if (analysis) setDisputeAnalysis(analysis);
    if (items.length > 0) {
      setStep('select');
      onStepChange('select');
    } else {
      toast({
        title: "No negative items found",
        description: "We couldn't identify any negative items on your credit report. Upload a different report or try again.",
      });
    }
  };

  const handleGenerateDisputes = (items: NegativeItem[]) => {
    setSelectedItems(items);
    setStep('documents');
    onStepChange('documents');
  };

  const handleDocumentsComplete = () => {
    setStep('generate');
    onStepChange('generate');
  };

  const handleDisputesComplete = () => {
    setStep('complete');
    onStepChange('complete');
    toast({
      title: "Disputes Saved",
      description: "Your AI-generated dispute letters have been created and saved successfully.",
    });
  };

  const handleManualItemCreated = (newItem: NegativeItem) => {
    setNegativeItems(prev => [...prev, newItem]);
    toast({
      title: "Item Added",
      description: "Dispute item has been added successfully.",
    });
    if (step === 'scan') {
      setStep('select');
      onStepChange('select');
    }
  };

  const handlePersonalInfoComplete = (info?: PersonalInfo) => {
    if (info) {
      setPersonalInfo(info);
    }
    setStep('scan');
    onStepChange('scan');
  };

  const skipDocumentsStep = () => {
    toast({
      title: "Documents Skipped",
      description: "You've chosen to skip the identity document submission step.",
    });
    setStep('generate');
    onStepChange('generate');
  };

  return (
    <>
      {step === 'personal' && (
        <PersonalInfoForm onComplete={handlePersonalInfoComplete} />
      )}

      {step === 'scan' && (
        <InputMethodTabs
          entryMethod={entryMethod}
          onMethodChange={(value) => setEntryMethod(value)}
          scanContent={<EnhancedDocumentScanner onNegativeItemsFound={handleScanComplete} />}
          manualContent={<ManualDisputeForm onItemCreated={handleManualItemCreated} />}
        />
      )}

      {step === 'select' && (
        <>
          <InputMethodTabs
            entryMethod={entryMethod}
            onMethodChange={(value) => setEntryMethod(value)}
            scanContent={<EnhancedDocumentScanner onNegativeItemsFound={handleScanComplete} />}
            manualContent={<ManualDisputeForm onItemCreated={handleManualItemCreated} />}
          />
          <EnhancedNegativeItemsList 
            items={negativeItems} 
            analysis={disputeAnalysis}
            onGenerateDisputes={handleGenerateDisputes} 
          />
        </>
      )}

      {step === 'documents' && (
        <>
          <UserDocumentsSection onComplete={handleDocumentsComplete} />
          <SkipDocumentsAlert onSkip={skipDocumentsStep} />
        </>
      )}

      {step === 'generate' && (
        <GenerateLettersSection
          selectedItems={selectedItems}
          personalInfo={personalInfo}
          onComplete={handleDisputesComplete}
          onBackToDocuments={() => {
            setStep('documents');
            onStepChange('documents');
          }}
          onBackToItems={() => {
            setStep('select');
            onStepChange('select');
          }}
        />
      )}

      {step === 'complete' && (
        <CompletionStep onRestart={onReset} />
      )}
    </>
  );
}
