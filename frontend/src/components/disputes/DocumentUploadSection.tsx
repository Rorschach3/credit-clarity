import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import { UserDocumentsSection } from "@/components/disputes/UserDocumentsSection";

interface DocumentUploadSectionProps {
  onClose: () => void;
}

export const DocumentUploadSection: React.FC<DocumentUploadSectionProps> = ({ onClose }) => {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div className={`mt-8 transition-all duration-500 ${collapsed ? "max-h-0 overflow-hidden opacity-0" : "max-h-[2000px] opacity-100"}`}>
      <div className="flex flex-col items-center mb-6">
        <Button
          variant="secondary"
          className="mb-4"
          onClick={() => {
            setCollapsed(true);
            setTimeout(() => {
              onClose();
            }, 600); // match transition duration
          }}
        >
          Skip Document Upload & Continue
        </Button>
        {collapsed && (
          <div className="w-full text-center text-green-700 bg-green-50 border border-green-200 rounded p-3 mt-2 transition-all duration-500">
            Document upload skipped. You may proceed to the next step.
          </div>
        )}
      </div>
      {!collapsed && (
        <>
          <h3 className="text-lg font-semibold mb-2 text-center">Upload Supporting Documents (Optional)</h3>
          <UserDocumentsSection />
          <div className="flex gap-2 mt-4">
            <Button variant="default">Prepare Dispute Packet</Button>
            <Button variant="outline" onClick={onClose}>Cancel</Button>
          </div>
        </>
      )}
    </div>
  );
};
